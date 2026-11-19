#!/usr/bin/env python3
"""Installer notre APK SmartTube Shorts Slider par ADB, sans désinstallation ni lancement."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request

REPOSITORY = 'valoche-68/SmartTube-Shorts-Slider'
API = 'https://api.github.com/repos/' + REPOSITORY
CERTIFICATE = '80a1a2db29be237b85486957804c21ddfa1a6c0371b93f2bd293e134aa138838'
ARCHES = ('armeabi-v7a', 'arm64-v8a', 'x86')


class InstallError(Exception):
    pass


def open_url(url):
    if not url.startswith('https://'):
        raise InstallError('Adresse de téléchargement non HTTPS refusée.')
    try:
        response = urllib.request.urlopen(urllib.request.Request(url, headers={
            'User-Agent': 'SmartTube-Shorts-Slider-installer',
            'Accept': 'application/vnd.github+json' if url.startswith(API + '/') else 'application/octet-stream'
        }), timeout=60)
        if not response.geturl().startswith('https://'):
            response.close()
            raise InstallError('Redirection non HTTPS refusée.')
        return response
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        raise InstallError('Téléchargement impossible ; vérifier Internet et réessayer. ' + str(error)) from error


def read_bytes(url, limit=4 * 1024 * 1024):
    with open_url(url) as response:
        data = response.read(limit + 1)
    if len(data) > limit:
        raise InstallError('Métadonnées anormalement volumineuses.')
    return data


def read_json(url):
    try:
        return json.loads(read_bytes(url))
    except (ValueError, UnicodeError) as error:
        raise InstallError('Métadonnées GitHub illisibles.') from error


def published_release(channel):
    candidates = [read_json(API + '/releases/latest')] if channel == 'stable' else read_json(API + '/releases?per_page=100')
    if not isinstance(candidates, list):
        raise InstallError('Liste de publications inconnue.')
    for item in candidates:
        if (isinstance(item, dict) and not item.get('draft', True) and
                item.get('prerelease') == (channel == 'beta') and
                re.fullmatch(r'v\d+(?:\.\d+)+-' + channel + r'-slider', item.get('tag_name', ''))):
            return item
    raise InstallError('Aucune publication Shorts Slider trouvée pour ce canal.')


def release_info(channel):
    release = published_release(channel)
    assets = release.get('assets', [])
    by_name = {asset['name']: asset for asset in assets}
    if len(by_name) != len(assets):
        raise InstallError('Fichiers de publication en double.')

    def asset(name):
        expected = 'https://github.com/' + REPOSITORY + '/releases/download/' + release['tag_name'] + '/' + name
        if name not in by_name or by_name[name].get('browser_download_url') != expected:
            raise InstallError('Fichier manquant ou adresse étrangère au projet : ' + name)
        return by_name[name]

    info = read_json(asset('build-info.json')['browser_download_url'])
    if not isinstance(info, dict):
        raise InstallError('Métadonnées de construction inconnues.')
    match = re.fullmatch(r'(\d+(?:\.\d+)+)-slider\.\d+', info.get('version_name', ''))
    if (not match or info.get('channel') != channel or info.get('tag') != release['tag_name'] or
            release['tag_name'] != 'v' + match[1] + '-' + channel + '-slider' or
            info.get('certificate_sha256') != CERTIFICATE or
            type(info.get('version_code')) is not int or not 0 < info['version_code'] < 2_100_000_000):
        raise InstallError('Identité ou version de publication incohérente.')
    try:
        sums = {}
        for line in read_bytes(asset('SHA256SUMS')['browser_download_url']).decode('utf-8').splitlines():
            digest, name = line.split()
            if name in sums or not re.fullmatch('[a-f0-9]{64}', digest):
                raise ValueError()
            sums[name] = digest
        records = info['apks']
        if len(records) != 4:
            raise ValueError()
        for arch in (*ARCHES, 'universal'):
            name = f'SmartTube_Shorts_Slider_{channel}_{match[1]}-slider_{arch}.apk'
            record = next(row for row in records if row['file'] == name)
            abis = sorted(ARCHES) if arch == 'universal' else [arch]
            if (record['architectures'] != abis or not re.fullmatch('[a-f0-9]{64}', record['sha256']) or
                    sums.get(name) != record['sha256']):
                raise ValueError()
            entry = asset(name)
            if type(entry.get('size')) is not int or not 0 < entry['size'] <= 256 * 1024 * 1024:
                raise ValueError()
    except (KeyError, TypeError, ValueError, StopIteration, UnicodeError) as error:
        raise InstallError('Architectures, empreintes ou fichiers APK incohérents.') from error
    return info, by_name


def download_apk(asset, sha256, destination):
    destination = Path(destination)
    digest = hashlib.sha256()
    total = 0
    created = False
    try:
        with open_url(asset['browser_download_url']) as response, destination.open('xb') as output:
            created = True
            while chunk := response.read(1024 * 1024):
                total += len(chunk)
                if total > asset['size']:
                    raise InstallError('Taille du téléchargement incohérente.')
                digest.update(chunk)
                output.write(chunk)
        if total != asset['size'] or digest.hexdigest() != sha256:
            raise InstallError('Empreinte SHA-256 ou taille incorrecte : aucune installation.')
    except BaseException:
        if created:
            destination.unlink(missing_ok=True)
        raise


class Adb:
    def __init__(self):
        self.executable = shutil.which('adb')
        self.serial = None
        if not self.executable:
            raise InstallError('ADB absent : lancer tools/start.sh ou tools/start.ps1 pour installer les prérequis.')

    def run(self, *args, check=True, timeout=30):
        command = [self.executable] + (['-s', self.serial] if self.serial else []) + list(args)
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired as error:
            raise InstallError('Délai ADB dépassé ; vérifier la connexion puis relancer, sans désinstaller.') from error
        if check and result.returncode:
            raise InstallError('Commande ADB échouée : ' + (result.stderr or result.stdout).strip())
        return result

    def devices(self):
        return [parts[:2] for line in self.run('devices').stdout.splitlines()[1:]
                if len(parts := line.split()) >= 2 and parts[1] in ('device', 'unauthorized', 'offline')]

    def select(self, serial=None, connect=None, noninteractive=False):
        devices = self.devices()
        if not devices and not serial and not connect and not noninteractive:
            print('Activez le débogage ADB sur la TV (et restez sur votre réseau local).')
            connect = input('Adresse IP de la TV, par exemple 192.168.1.5 : ').strip()
        if connect:
            if not re.fullmatch(r'[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?(?::\d{1,5})?', connect):
                raise InstallError('Adresse attendue : IP ou nom, éventuellement suivi de :port.')
            target = connect if ':' in connect else connect + ':5555'
            connection = self.run('connect', target, check=False)
            serial = serial or target
            devices = self.devices()
            if connection.returncode and not any(device == target for device, _ in devices):
                raise InstallError('Connexion ADB impossible ; vérifier IP, port et débogage sur la TV, puis relancer.')
        if any(state == 'unauthorized' and (not serial or device == serial) for device, state in devices):
            if noninteractive:
                raise InstallError('Accepter la demande de débogage ADB sur la TV, puis relancer.')
            input('Acceptez « Autoriser le débogage USB » sur la TV, puis appuyez sur Entrée ici : ')
            devices = self.devices()
        available = [device for device, state in devices if state == 'device']
        if serial:
            if serial not in available:
                raise InstallError('Cet appareil est absent, hors ligne ou non autorisé ; vérifier IP et débogage ADB.')
            self.serial = serial
        elif len(available) == 1:
            self.serial = available[0]
        elif available and not noninteractive:
            for index, device in enumerate(available, 1):
                print(f'  {index}. {device}')
            number = input('Plusieurs appareils : numéro de la TV à utiliser : ').strip()
            if not number.isdigit() or not 1 <= int(number) <= len(available):
                raise InstallError('Sélection invalide ; aucun appareil modifié.')
            self.serial = available[int(number) - 1]
        else:
            raise InstallError('Sélectionner une TV avec --connect IP ou un appareil déjà connecté avec --device IDENTIFIANT.')

    def prop(self, name):
        return self.run('shell', 'getprop', name).stdout.strip()

    def installed(self, package):
        listing = self.run('shell', 'pm', 'list', 'packages', package).stdout.splitlines()
        if 'package:' + package not in listing:
            return None
        data = self.run('shell', 'dumpsys', 'package', package).stdout
        fields = {}
        for key in ('versionName', 'versionCode', 'userId', 'firstInstallTime'):
            match = re.search(r'\b' + key + r'=([^\r\n]+)', data)
            fields[key] = match[1].strip() if match else None
        if not fields['versionCode'] or not fields['versionName']:
            raise InstallError('Version installée illisible ; aucune installation lancée.')
        fields['versionCode'] = int(fields['versionCode'].split()[0])
        return fields


def choose_arch(abilist):
    for arch in abilist.split(','):
        if arch.strip() in ARCHES:
            return arch.strip()
    raise InstallError('Architecture Android non prise en charge : ' + abilist)


def check_upgrade(installed, info):
    if installed is None:
        return True
    if not re.fullmatch(r'\d+(?:\.\d+)+-slider\.\d+', installed['versionName']):
        raise InstallError('Une application officielle ou une autre variante occupe ce canal. '
                           'Aucune désinstallation automatique : consulter le guide de migration avant de continuer.')
    if installed['versionCode'] > info['version_code']:
        raise InstallError('La version installée est plus récente : rétrogradation refusée.')
    if installed['versionCode'] == info['version_code']:
        if installed['versionName'] != info['version_name']:
            raise InstallError('Versions incohérentes ; vérifier l’application installée.')
        return False
    return True


def install(adb, apk, package, info, before):
    result = adb.run('install', '-r', str(apk), check=False, timeout=240)
    if result.returncode or 'Success' not in result.stdout.splitlines():
        details = (result.stdout + '\n' + result.stderr).strip()
        raise InstallError('Installation refusée par Android. Aucune désinstallation ni tentative forcée. ' + details)
    after = adb.installed(package)
    if after is None or after['versionCode'] != info['version_code'] or after['versionName'] != info['version_name']:
        raise InstallError('Installation terminée mais version non confirmée ; vérifier la TV avant de relancer.')
    if before:
        for key in ('userId', 'firstInstallTime'):
            if before.get(key) and before[key] != after.get(key):
                raise InstallError('Identité des données modifiée ; vérifier le compte et les réglages sur la TV.')
    print('Installation vérifiée. Application non lancée. Ouvrez Shorts Slider sur la TV quand vous le souhaitez.')


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(errors='backslashreplace')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--channel', choices=('stable', 'beta'), default='stable', help='Stable par défaut')
    parser.add_argument('--connect', metavar='IP[:PORT]', help='Connexion ADB réseau (port 5555 par défaut)')
    parser.add_argument('--device', help='Identifiant ADB d’un appareil déjà connecté')
    parser.add_argument('--yes', action='store_true', help='Confirmer sans question ; exige un appareil non ambigu')
    parser.add_argument('--dry-run', action='store_true', help='Lire la TV et la release, sans télécharger ni installer l’APK')
    parser.add_argument('--download-only', action='store_true', help='Télécharger et vérifier l’APK, sans ADB')
    parser.add_argument('--arch', choices=(*ARCHES, 'universal'), help='Architecture pour --download-only (universal par défaut)')
    parser.add_argument('--output', type=Path, help='Nouveau fichier APK pour --download-only')
    args = parser.parse_args(argv)
    if (args.arch or args.output) and not args.download_only:
        parser.error('--arch et --output nécessitent --download-only ; sur TV l’architecture est détectée.')
    if args.download_only and args.dry_run:
        parser.error('Choisir --download-only ou --dry-run.')
    package = 'org.smarttube.' + args.channel
    adb = None
    before = None
    arch = args.arch or 'universal'
    if not args.download_only:
        adb = Adb()
        adb.select(args.device, args.connect, args.yes)
        arch = choose_arch(adb.prop('ro.product.cpu.abilist') or adb.prop('ro.product.cpu.abi'))
        before = adb.installed(package)
        print('TV : ' + adb.prop('ro.product.model') + ' — ' + adb.serial)
    print('Canal Shorts Slider : ' + args.channel)
    info, assets = release_info(args.channel)
    record = next(row for row in info['apks'] if row['architectures'] == (sorted(ARCHES) if arch == 'universal' else [arch]))
    print('Version : ' + info['version_name'] + ' — ' + arch)
    if before:
        print('Version installée : ' + before['versionName'])
    if not check_upgrade(before, info):
        print('Cette version de Shorts Slider est déjà installée ; rien à modifier.')
        return 0
    if args.dry_run:
        print('Simulation terminée : aucune installation et aucun lancement.')
        return 0
    if args.download_only:
        destination = args.output or Path.cwd() / record['file']
        download_apk(assets[record['file']], record['sha256'], destination)
        print('APK vérifié : ' + str(destination.resolve()))
        return 0
    with tempfile.TemporaryDirectory(prefix='shorts-slider-install-') as temporary:
        apk = Path(temporary) / record['file']
        print('Téléchargement de notre APK et vérification SHA-256…')
        download_apk(assets[record['file']], record['sha256'], apk)
        if not args.yes and input('Installer sur cette TV sans lancer l’application ? [o/N] : ').strip().lower() not in ('o', 'oui', 'y', 'yes'):
            print('Annulé ; aucune installation.')
            return 0
        install(adb, apk, package, info, before)
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (InstallError, OSError, KeyError, TypeError, ValueError) as error:
        print('Arrêt : ' + str(error), file=sys.stderr)
        raise SystemExit(1)
    except (KeyboardInterrupt, EOFError):
        print('\nAnnulé ; aucune désinstallation.', file=sys.stderr)
        raise SystemExit(130)
