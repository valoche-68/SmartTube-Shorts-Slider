#!/usr/bin/env python3
"""Configure les Shorts dans SmartTube officiel via une sauvegarde et ADB, sans root."""
import argparse
import copy
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shlex
import shutil
import stat
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
import zipfile

SUPPORTED = {"32.56": 2446}  # Verified against upstream tags 32.56 and 32.56s.
DELIM = "%OB%"
TWEAKS = "video_player_tweaks_data"
PLAYER = "video_player_data"
GENERAL = "general_data"
FIELDS = {"loop": (TWEAKS, 44, "true"), "horizontal": (TWEAKS, 45, "true"),
          "vertical": (TWEAKS, 57, "false"), "section": (TWEAKS, 31, "défaut natif selon la mémoire"),
          "up_down_action": (GENERAL, 51, "-1"), "left_volume": (GENERAL, 54, "false"),
          "playback": (PLAYER, 51, "2")}


class ConfigError(Exception):
    pass


def private_write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(data)


class Backup:
    def __init__(self, data, package, profile=None):
        self.package = package
        self.entries = {}
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                total = 0
                for item in archive.infolist():
                    path = PurePosixPath(item.filename)
                    total += item.file_size
                    if (path.is_absolute() or ".." in path.parts or "\\" in item.filename or
                            ":" in item.filename or stat.S_ISLNK(item.external_attr >> 16) or
                            total > 200 * 1024 * 1024 or item.file_size > 32 * 1024 * 1024):
                        raise ConfigError("Archive non sûre ou trop volumineuse.")
                    if item.filename in self.entries:
                        raise ConfigError("Archive ambiguë : entrée en double.")
                    self.entries[item.filename] = archive.read(item)
        except (zipfile.BadZipFile, RuntimeError, OSError) as exc:
            raise ConfigError("Sauvegarde ZIP illisible ou incomplète.") from exc
        matches = [name for name in self.entries if name.endswith("shared_prefs/" + package + "_preferences.xml")]
        if len(matches) != 1:
            raise ConfigError("Il faut une sauvegarde complète et unique du canal choisi.")
        self.xml_path = matches[0]
        self.root = self.xml_path.rsplit("shared_prefs/", 1)[0]
        raw = self.entries[self.xml_path]
        if b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper():
            raise ConfigError("XML avec entités non pris en charge.")
        try:
            self.xml = ET.fromstring(raw)
        except ET.ParseError as exc:
            raise ConfigError("Préférences XML invalides.") from exc
        if self.xml.tag != "map":
            raise ConfigError("Format XML de préférences inconnu.")
        keys = [e.get("name") for e in self.xml]
        if len(keys) != len(set(keys)):
            raise ConfigError("Préférences ambiguës : clés en double.")
        if not any(name.startswith(self.root + "files/app_prefs/") for name in self.entries) and not any(
                (element.get("name") or "").endswith((TWEAKS, PLAYER, GENERAL)) for element in self.xml):
            raise ConfigError("Sauvegarde sans réglages d'application : créer une sauvegarde complète récente.")
        self.xml_changed = False
        self.xml_values = {e.get("name"): e for e in self.xml}
        multi = self.xml_values.get("multi_profiles")
        enabled = multi is not None and multi.get("value") == "true"
        selected = self.xml_values.get("last_profile_name")
        active = selected.text if enabled and selected is not None else ""
        self.profile = active if profile is None else profile
        self.profile = self.profile or ""
        if any(c in self.profile for c in "/\\\x00") or self.profile in (".", ".."):
            raise ConfigError("Nom de profil non pris en charge.")
        if profile is not None and profile != active and not self.has_profile(profile):
            raise ConfigError("Profil absent de la sauvegarde.")
        if self.get_slot(TWEAKS, 61) in ("true", "false"):
            raise ConfigError("Cette sauvegarde contient des réglages personnalisés. Utiliser cet outil avec SmartTube officiel.")

    def has_profile(self, profile):
        key = (profile + "_" if profile else "") + TWEAKS
        return self.root + "files/app_prefs/" + key in self.entries or key in self.xml_values

    def location(self, name):
        key = (self.profile + "_" if self.profile else "") + name
        return self.root + "files/app_prefs/" + key, key

    def slots(self, name):
        path, key = self.location(name)
        element = self.xml_values.get(key)
        text = self.entries[path].decode("utf-8") if path in self.entries else (element.text if element is not None else None)
        if text is None or text == "":
            return []
        if DELIM not in text or len(text.split(DELIM)) > 128:
            raise ConfigError("Format de réglages inconnu ; aucune modification appliquée.")
        return text.split(DELIM)

    def get_slot(self, name, index):
        values = self.slots(name)
        return values[index] if index < len(values) else "null"

    def set_slot(self, name, index, value):
        values = self.slots(name)
        if index >= len(values):
            values.extend(["null"] * (index + 1 - len(values)))
        values[index] = value
        path, key = self.location(name)
        text = DELIM.join(values)
        if path in self.entries or key not in self.xml_values:
            self.entries[path] = text.encode()
        else:
            self.xml_values[key].text = text
            self.xml_changed = True

    def state(self):
        return {key: self.get_slot(name, index) for key, (name, index, _) in FIELDS.items()}

    def effective(self, key):
        name, index, default = FIELDS[key]
        value = self.get_slot(name, index)
        return default if value in ("null", "") else value

    def encode(self):
        entries = dict(self.entries)
        if self.xml_changed:
            entries[self.xml_path] = ET.tostring(self.xml, encoding="utf-8", xml_declaration=True)
        result = io.BytesIO()
        with zipfile.ZipFile(result, "w", zipfile.ZIP_DEFLATED) as archive:
            for name, value in entries.items():
                archive.writestr(name, value)
        return result.getvalue()


def configure(backup, navigation=None, autoplay=None, section=None):
    before = backup.state()
    changes = {}
    if navigation:
        changes.update(vertical=str(navigation == "up-down").lower(), horizontal=str(navigation == "left-right").lower())
        if navigation == "up-down": changes["up_down_action"] = "-1"
        if navigation == "left-right": changes["left_volume"] = "false"
    if autoplay is not None:
        changes["loop"] = "false" if autoplay else "true"
        if autoplay: changes["playback"] = "2"  # Native global 'play next' mode.
    if section is not None:
        changes["section"] = str(section).lower()
    for key, value in changes.items():
        name, index, _ = FIELDS[key]
        backup.set_slot(name, index, value)
    return {key: {"before": before[key], "after": backup.state()[key]} for key in changes if before[key] != backup.state()[key]}


def undo(backup, record):
    if record.get("package") != backup.package or record.get("profile") != backup.profile or record.get("schema") != 1:
        raise ConfigError("Annulation incompatible avec ce canal ou ce profil.")
    for key, change in record["changes"].items():
        if key not in FIELDS or not re.fullmatch(r"true|false|null|-?\d+", change["before"]):
            raise ConfigError("Journal d'annulation invalide.")
        if backup.state()[key] != change["after"]:
            raise ConfigError("Un réglage ciblé a changé depuis : annulation interrompue pour le préserver.")
    for key, change in record["changes"].items():
        name, index, _ = FIELDS[key]
        backup.set_slot(name, index, change["before"])
    return {key: {"before": change["after"], "after": change["before"]} for key, change in record["changes"].items()}


class Adb:
    def __init__(self, serial=None):
        self.executable = shutil.which("adb")
        if not self.executable:
            raise ConfigError("ADB absent. Installer Android SDK Platform Tools, puis ajouter adb au PATH.")
        devices = self.run("devices").stdout.splitlines()[1:]
        available = [line.split()[0] for line in devices if len(line.split()) >= 2 and line.split()[1] == "device"]
        if serial and serial not in available:
            raise ConfigError("Appareil non connecté ou non autorisé. Exécuter adb connect / adb pair et accepter sur la TV.")
        if not serial and len(available) != 1:
            raise ConfigError("Choisir un appareil connecté avec --device ; sélection automatique uniquement s'il est unique.")
        self.serial = serial or available[0]

    def run(self, *args, check=True):
        command = [self.executable]
        if getattr(self, "serial", None): command += ["-s", self.serial]
        result = subprocess.run(command + list(args), capture_output=True, text=True)
        if check and result.returncode:
            raise ConfigError("Commande ADB échouée : " + args[0])
        return result

    def shell(self, *args, check=True):
        return self.run("shell", " ".join(shlex.quote(arg) for arg in args), check=check)

    def version(self, package):
        data = self.shell("dumpsys", "package", package).stdout
        name = re.search(r"versionName=([^\s]+)", data)
        code = re.search(r"versionCode=(\d+)", data)
        if not name or not code or SUPPORTED.get(name[1]) != int(code[1]):
            raise ConfigError("Version officielle non vérifiée. Utiliser les réglages manuels décrits dans le guide.")
        return name[1]


def choice(prompt, values, default):
    answer = input(prompt + " [" + "/".join(values) + "] (" + default + ") : ").strip().lower() or default
    if answer not in values:
        raise ConfigError("Choix non reconnu ; relancer le script.")
    return answer


def main(argv=None):
    # Older Windows consoles and redirected output may use a legacy encoding.
    # An unrepresentable character in a path or message must not abort a backup.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="backslashreplace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", help="Identifiant adb de la TV déjà connectée")
    parser.add_argument("--channel", choices=["stable", "beta"], default="stable")
    parser.add_argument("--backup", type=Path, help="ZIP local (sinon guidage ADB)")
    parser.add_argument("--version", help="Version officielle du ZIP local ; exigée hors connexion")
    parser.add_argument("--profile", help="Profil actif par défaut ; chaîne vide pour les réglages communs")
    parser.add_argument("--navigation", choices=["up-down", "left-right", "off"])
    parser.add_argument("--autoplay", choices=["on", "off"])
    parser.add_argument("--section", choices=["on", "off"])
    parser.add_argument("--undo", type=Path, help="Journal undo.json à réappliquer sur une sauvegarde récente")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--dry-run", action="store_true", help="Lecture et simulation uniquement, aucun transfert ni fichier créé")
    parser.add_argument("--output", type=Path, help="Nouveau dossier privé de résultat")
    args = parser.parse_args(argv)
    package = "org.smarttube." + args.channel
    adb = None
    source = args.backup
    if source:
        if args.version not in SUPPORTED:
            raise ConfigError("Indiquer --version avec une version vérifiée : " + ", ".join(SUPPORTED))
        original = source.read_bytes()
    else:
        adb = Adb(args.device)
        args.version = adb.version(package)
        print("Dans SmartTube : Paramètres > Sauvegarde/restauration > Sauvegarde locale.")
        print("Créez maintenant une sauvegarde complète, puis indiquez le chemin ZIP affiché sur la TV.")
        remote = input("Chemin complet du ZIP sur la TV : ").strip()
        if not remote.startswith(("/sdcard/", "/storage/emulated/0/")) or not remote.endswith(".zip"):
            raise ConfigError("Chemin ZIP externe attendu.")
        result = subprocess.run([adb.executable, "-s", adb.serial, "exec-out", "cat " + shlex.quote(remote)], capture_output=True)
        if result.returncode or not result.stdout:
            raise ConfigError("Sauvegarde inaccessible. Copier son ZIP sur le PC et utiliser --backup et --version.")
        original = result.stdout
    backup = Backup(original, package, args.profile)
    stored_code = backup.get_slot(GENERAL, 39)
    if stored_code not in ("null", "", str(SUPPORTED[args.version])):
        raise ConfigError("La version mémorisée dans la sauvegarde ne correspond pas à la version annoncée.")
    print("Réglages natifs : haut/bas=" + backup.effective("vertical") + ", gauche/droite=" + backup.effective("horizontal") +
          ", boucle=" + backup.effective("loop") + ", section-playlist=" + backup.effective("section"))
    if args.status: return 0
    interactive = not any([args.navigation, args.autoplay, args.section, args.undo])
    if interactive:
        action = choice("Action : configurer, consulter seulement ou annuler des changements précédents",
                        ["configurer", "consulter", "annuler"], "configurer")
        if action == "consulter": return 0
        if action == "annuler": args.undo = Path(input("Chemin du journal undo.json : ").strip())
        else:
            args.navigation = choice("Navigation Shorts (off = désactivée)", ["up-down", "left-right", "off"], "up-down")
            args.autoplay = choice("Enchaîner automatiquement (off = boucle)", ["on", "off"], "on")
            args.section = choice("Utiliser la section actuelle comme playlist", ["on", "off"], "on")
    if args.undo:
        changes = undo(backup, json.loads(args.undo.read_text()))
    else:
        changes = configure(backup, args.navigation, None if args.autoplay is None else args.autoplay == "on",
                            None if args.section is None else args.section == "on")
    if not changes:
        print("Les réglages demandés sont déjà appliqués.")
        return 0
    for key, value in changes.items(): print(f"  {key}: {value['before']} -> {value['after']}")
    if "playback" in changes:
        print("Le mode natif ‘vidéo suivante’ concerne aussi les vidéos longues. La boucle reste propre aux Shorts.")
    print("Aucun bouton ajouté et aucune préparation anticipée ajoutée à l'application officielle.")
    if args.dry_run:
        print("Simulation terminée : aucun fichier écrit et aucune restauration lancée.")
        return 0
    if interactive and choice("Préparer la sauvegarde modifiée ?", ["oui", "non"], "oui") != "oui": return 0
    base = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / ".local/share"))) / "smarttube-shorts-slider"
    output = args.output or base / time.strftime("%Y%m%d-%H%M%S")
    output.mkdir(parents=True, exist_ok=False, mode=0o700)
    private_write(output / "original.zip", original)
    private_write(output / "configured.zip", backup.encode())
    private_write(output / "undo.json", json.dumps({"schema": 1, "package": package, "profile": backup.profile,
                  "version": args.version, "source_sha256": hashlib.sha256(original).hexdigest(), "changes": changes}, indent=2).encode())
    print("Résultat privé : " + str(output.resolve()))
    print("Conserver original.zip et undo.json ; ces fichiers peuvent contenir des données de compte. Ne pas les publier.")
    if adb and choice("Envoyer configured.zip et ouvrir l'import officiel sur la TV ?", ["oui", "non"], "oui") == "oui":
        remote = "/sdcard/Android/media/" + package + "/ShortsSlider/" + output.name + ".zip"
        adb.shell("mkdir", "-p", str(PurePosixPath(remote).parent))
        adb.run("push", str(output / "configured.zip"), remote)
        adb.shell("am", "start", "-n", package + "/com.liskovsoft.smartyoutubetv2.common.misc.BackupReceiverActivity",
                  "-a", "android.intent.action.VIEW", "-d", "file://" + remote, "-t", "application/zip")
        print("Valider la restauration sur la TV, puis relancer SmartTube. L'application se ferme normalement après restauration.")
        input("Après validation et fermeture de l'application, Entrée pour retirer le ZIP temporaire de la TV : ")
        adb.shell("rm", "-f", remote)
    else:
        print("Importer configured.zip avec le mécanisme officiel, puis vérifier les réglages sur la TV.")
    print("Pour annuler : créer une nouvelle sauvegarde et relancer avec --undo " + str(output / "undo.json"))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ConfigError, OSError, UnicodeError, ValueError, EOFError) as exc:
        print("Arrêt : " + str(exc), file=sys.stderr)
        sys.exit(2)
