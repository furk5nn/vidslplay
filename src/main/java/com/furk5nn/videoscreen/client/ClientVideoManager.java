package com.furk5nn.videoscreen.client;

import java.io.File;
import java.util.HashMap;
import java.util.Map;
import net.minecraft.client.Minecraft;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import org.lwjgl.util.tinyfd.TinyFileDialogs;

public final class ClientVideoManager {
    public static final ClientVideoManager INSTANCE = new ClientVideoManager();
    private final Map<Long, LocalVideoPlayer> players = new HashMap<>();

    private ClientVideoManager() {}

    public void interact(Level level, BlockPos pos, BlockState state) {
        PanelLayout panel = PanelLayout.find(level, pos, state);
        LocalVideoPlayer current = players.get(panel.root().asLong());

        if (Minecraft.getInstance().options.keyShift.isDown() && current != null) {
            current.togglePause();
            message(current.isPaused() ? "Video paused" : "Video playing");
            return;
        }

        String selected = TinyFileDialogs.tinyfd_openFileDialog(
            "Choose MP4 video", "", null, null, false
        );
        if (selected == null || selected.isBlank()) return;
        if (!selected.toLowerCase().endsWith(".mp4")) {
            message("Please choose an .mp4 file");
            return;
        }

        LocalVideoPlayer old = players.remove(panel.root().asLong());
        if (old != null) old.close();
        players.put(panel.root().asLong(), new LocalVideoPlayer(new File(selected)));
        message("Loaded: " + new File(selected).getName() + "  |  Shift + right click = pause/play");
    }

    public LocalVideoPlayer playerFor(PanelLayout panel) {
        return players.get(panel.root().asLong());
    }

    private static void message(String text) {
        if (Minecraft.getInstance().player != null) {
            Minecraft.getInstance().player.displayClientMessage(Component.literal(text), true);
        }
    }
}
