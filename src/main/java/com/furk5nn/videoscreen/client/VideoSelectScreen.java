package com.furk5nn.videoscreen.client;

import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;

public final class VideoSelectScreen extends Screen {
    private final PanelLayout panel;

    public VideoSelectScreen(PanelLayout panel) {
        super(Component.literal("Video Screen"));
        this.panel = panel;
    }

    @Override
    protected void init() {
        int centerX = width / 2;
        int centerY = height / 2;

        addRenderableWidget(Button.builder(
            Component.literal("Choose local video (" + panel.width() + "x" + panel.height() + ")"),
            button -> {
                ClientVideoManager.INSTANCE.chooseVideo(panel);
                onClose();
            }
        ).bounds(centerX - 110, centerY - 12, 220, 20).build());

        addRenderableWidget(Button.builder(
            Component.literal("Close"),
            button -> onClose()
        ).bounds(centerX - 110, centerY + 16, 220, 20).build());
    }
}
