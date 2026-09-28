package dev.localvideo.screens.client;

import net.minecraft.client.Minecraft;
import org.lwjgl.PointerBuffer;
import org.lwjgl.system.MemoryStack;
import org.lwjgl.util.tinyfd.TinyFileDialogs;

import java.io.File;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.function.Consumer;

final class NativeVideoPicker {
    private static final ExecutorService PICKER = Executors.newSingleThreadExecutor(r -> {
        Thread t = new Thread(r, "LocalVideoScreens-FilePicker");
        t.setDaemon(true);
        return t;
    });

    private static final String[] MEDIA_PATTERNS = {
            "*.mp4", "*.webm", "*.m4v", "*.mov", "*.mkv", "*.avi", "*.jpg", "*.jpeg", "*.png", "*.gif", "*.webp", "*.bmp"
    };

    private NativeVideoPicker() {}

    static void choose(Consumer<File> callback) {
        PICKER.execute(() -> {
            File selected = null;
            try (MemoryStack stack = MemoryStack.stackPush()) {
                PointerBuffer filters = stack.mallocPointer(MEDIA_PATTERNS.length);
                for (String pattern : MEDIA_PATTERNS) {
                    filters.put(stack.UTF8(pattern));
                }
                filters.flip();

                String result = TinyFileDialogs.tinyfd_openFileDialog(
                        "Medya seç",
                        "",
                        filters,
                        "Video ve resim dosyaları",
                        false
                );

                if (result != null && !result.isBlank()) {
                    selected = new File(result);
                }
            } catch (Throwable t) {
                t.printStackTrace();
            }

            File finalSelected = selected;
            Minecraft.getInstance().execute(() -> callback.accept(finalSelected));
        });
    }
}
