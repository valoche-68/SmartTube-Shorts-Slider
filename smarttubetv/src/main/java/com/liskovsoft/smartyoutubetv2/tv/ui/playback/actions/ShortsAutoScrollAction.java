package com.liskovsoft.smartyoutubetv2.tv.ui.playback.actions;

import android.content.Context;
import com.liskovsoft.smartyoutubetv2.tv.R;

public class ShortsAutoScrollAction extends TwoStateAction {
    public ShortsAutoScrollAction(Context context) {
        super(context, R.id.action_shorts_auto_scroll, R.drawable.action_shorts_auto_scroll, false);

        String[] labels = new String[2];
        labels[INDEX_OFF] = context.getString(R.string.action_shorts_auto_scroll);
        labels[INDEX_ON] = context.getString(R.string.action_shorts_auto_scroll);
        setLabels(labels);
    }
}
