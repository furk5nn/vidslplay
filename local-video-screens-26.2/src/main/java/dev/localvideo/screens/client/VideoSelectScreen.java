package dev.localvideo.screens.client;

import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;

public final class VideoSelectScreen extends Screen {
    private final ScreenGeometry geometry;
    private boolean pickerOpen;

    public VideoSelectScreen(ScreenGeometry geometry) {
        super(Component.literal("Local Video Screen"));
        this.geometry = geometry;
    }

    @Override
    protected void init() {
        int centerX = width / 2;
        int centerY = height / 2;

        addRenderableWidget(Button.builder(
                Component.literal("Video seç (" + geometry.width() + "x" + geometry.height() + ")"),
                button -> openPicker()
        ).bounds(centerX - 100, centerY - 12, 200, 20).build());

        addRenderableWidget(Button.builder(Component.literal("Kapat"), button -> onClose())
                .bounds(centerX - 100, centerY + 16, 200, 20).build());
    }

    private void openPicker() {
        if (pickerOpen) return;
        pickerOpen = true;
        NativeVideoPicker.choose(file -> {
            pickerOpen = false;
            if (file == null) return;
            VideoScreenManager.get().play(geometry, file);
            onClose();
        });
    }
}
