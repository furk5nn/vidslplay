package com.furk5nn.videoscreen.client;

import java.io.File;
import java.util.HashMap;
import java.util.Map;
import net.minecraft.client.Minecraft;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import org.lwjgl.util.tinyfd.TinyFileDialogs;

public final class ClientVideoManager {
    public static final ClientVideoManager INSTANCE = new ClientVideoManager();
    private final Map<Long, WaterMediaVideoPlayer> players = new HashMap<>();

    private ClientVideoManager() {}

    public void interact(Level level, BlockPos pos, BlockState state) {
        PanelLayout panel = PanelLayout.find(level, pos, state);
        long key = panel.root().asLong();
        WaterMediaVideoPlayer current = players.get(key);

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

        try {
            WaterMediaVideoPlayer old = players.remove(key);
            if (old != null) old.close();

            WaterMediaVideoPlayer player = new WaterMediaVideoPlayer(new File(selected));
            players.put(key, player);
            message("Loaded: " + new File(selected).getName() + " | Shift + right click = pause/play");
        } catch (Exception e) {
            e.printStackTrace();
            message("Could not open video: " + e.getMessage());
        }
    }

    public WaterMediaVideoPlayer playerFor(PanelLayout panel) {
        WaterMediaVideoPlayer player = players.get(panel.root().asLong());
        if (player != null) player.tickInit();
        return player;
    }

    private static void message(String text) {
        System.out.println("[VideoScreen] " + text);
    }
}
