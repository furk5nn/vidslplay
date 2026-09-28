package dev.localvideo.screens.client;

import dev.localvideo.screens.ScreenFillNetworking;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.components.EditBox;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;

public final class ScreenFillConfirmScreen extends Screen {
    private final BlockPos origin;
    private final int facingId;

    private EditBox widthBox;
    private EditBox heightBox;

    public ScreenFillConfirmScreen(BlockPos origin, int facingId) {
        super(Component.literal("Ekran oluştur"));
        this.origin = origin;
        this.facingId = facingId;
    }

    @Override
    protected void init() {
        int centerX = width / 2;
        int centerY = height / 2;

        widthBox = new EditBox(font, centerX - 100, centerY - 42, 95, 20, Component.literal("Genişlik"));
        widthBox.setValue("12");
        widthBox.setMaxLength(2);
        widthBox.setFilter(ScreenFillConfirmScreen::digitsOnly);
        addRenderableWidget(widthBox);

        heightBox = new EditBox(font, centerX + 5, centerY - 42, 95, 20, Component.literal("Yükseklik"));
        heightBox.setValue("6");
        heightBox.setMaxLength(2);
        heightBox.setFilter(ScreenFillConfirmScreen::digitsOnly);
        addRenderableWidget(heightBox);

        addRenderableWidget(Button.builder(
                Component.literal("Oluştur"),
                button -> createScreen()
        ).bounds(centerX - 100, centerY - 12, 200, 20).build());

        addRenderableWidget(Button.builder(
                Component.literal("İptal"),
                button -> onClose()
        ).bounds(centerX - 100, centerY + 16, 200, 20).build());
    }

    private void createScreen() {
        int w = parse(widthBox.getValue());
        int h = parse(heightBox.getValue());
        if (w < 1 || h < 1) return;

        ScreenFillNetworking.confirm(origin, facingId, w, h);
        onClose();
    }

    private static int parse(String value) {
        try {
            return Integer.parseInt(value);
        } catch (NumberFormatException ignored) {
            return 0;
        }
    }

    private static boolean digitsOnly(String value) {
        if (value.isEmpty()) return true;
        for (int i = 0; i < value.length(); i++) {
            if (!Character.isDigit(value.charAt(i))) return false;
        }
        return true;
    }
}
