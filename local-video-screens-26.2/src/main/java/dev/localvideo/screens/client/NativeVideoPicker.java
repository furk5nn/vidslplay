package dev.localvideo.screens.client;

import net.minecraft.client.Minecraft;

import java.awt.FileDialog;
import java.awt.Frame;
import java.io.File;
import java.io.FilenameFilter;
import java.util.Locale;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.function.Consumer;

final class NativeVideoPicker {
    private static final ExecutorService PICKER = Executors.newSingleThreadExecutor(r -> {
        Thread t = new Thread(r, "LocalVideoScreens-FilePicker");
        t.setDaemon(true);
        return t;
    });

    private static final FilenameFilter VIDEO_FILTER = (dir, name) -> {
        String n = name.toLowerCase(Locale.ROOT);
        return n.endsWith(".mp4") || n.endsWith(".webm") || n.endsWith(".m4v")
                || n.endsWith(".mov") || n.endsWith(".mkv") || n.endsWith(".avi");
    };

    private NativeVideoPicker() {}

    static void choose(Consumer<File> callback) {
        PICKER.execute(() -> {
            File selected = null;
            Frame owner = new Frame();
            try {
                FileDialog dialog = new FileDialog(owner, "Video seç", FileDialog.LOAD);
                dialog.setFilenameFilter(VIDEO_FILTER);
                dialog.setVisible(true);
                if (dialog.getFile() != null && dialog.getDirectory() != null) {
                    selected = new File(dialog.getDirectory(), dialog.getFile());
                }
                dialog.dispose();
            } finally {
                owner.dispose();
            }

            File finalSelected = selected;
            Minecraft.getInstance().execute(() -> callback.accept(finalSelected));
        });
    }
}
