package dev.localvideo.screens.client;

import dev.localvideo.screens.ScreenFillNetworking;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;

public final class ScreenFillConfirmScreen extends Screen {
    private final BlockPos a;
    private final BlockPos b;
    private final int screenWidth;
    private final int screenHeight;

    public ScreenFillConfirmScreen(BlockPos a, BlockPos b, int screenWidth, int screenHeight) {
        super(Component.literal("Ekran alanını doldur"));
        this.a = a;
        this.b = b;
        this.screenWidth = screenWidth;
        this.screenHeight = screenHeight;
    }

    @Override
    protected void init() {
        int centerX = width / 2;
        int centerY = height / 2;

        addRenderableWidget(Button.builder(
                Component.literal("Doldur (" + screenWidth + "x" + screenHeight + ")"),
                button -> {
                    ScreenFillNetworking.confirm(a, b);
                    onClose();
                }
        ).bounds(centerX - 100, centerY - 12, 200, 20).build());

        addRenderableWidget(Button.builder(
                Component.literal("İptal"),
                button -> onClose()
        ).bounds(centerX - 100, centerY + 16, 200, 20).build());
    }
}
