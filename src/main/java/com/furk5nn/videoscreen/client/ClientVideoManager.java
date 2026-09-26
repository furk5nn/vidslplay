package com.furk5nn.videoscreen.client;

import de.keksuccino.rinku.Rinku;
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
    private final Map<Long, ChromiumVideoPlayer> players = new HashMap<>();

    private ClientVideoManager() {}

    public void interact(Level level, BlockPos pos, BlockState state) {
        PanelLayout panel = PanelLayout.find(level, pos, state);
        long key = panel.root().asLong();
        ChromiumVideoPlayer current = players.get(key);

        if (Minecraft.getInstance().options.keyShift.isDown() && current != null) {
            current.togglePause();
            message(current.isPaused() ? "Video paused" : "Video playing");
            return;
        }

        if (!Rinku.isInitialized()) {
            message("Rinku/Chromium is still initializing. Try again in a few seconds.");
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
            ChromiumVideoPlayer old = players.remove(key);
            if (old != null) old.close();

            int width = Math.min(1920, Math.max(640, panel.width() * 160));
            int height = Math.min(1080, Math.max(360, panel.height() * 160));
            ChromiumVideoPlayer player = new ChromiumVideoPlayer(new File(selected), width, height);
            players.put(key, player);
            message("Loaded: " + new File(selected).getName() + " | Shift + right click = pause/play");
        } catch (Exception e) {
            e.printStackTrace();
            message("Could not open video: " + e.getMessage());
        }
    }

    public ChromiumVideoPlayer playerFor(PanelLayout panel) {
        ChromiumVideoPlayer player = players.get(panel.root().asLong());
        if (player != null) {
            int width = Math.min(1920, Math.max(640, panel.width() * 160));
            int height = Math.min(1080, Math.max(360, panel.height() * 160));
            player.resize(width, height);
        }
        return player;
    }

    private static void message(String text) {
        System.out.println("[VideoScreen] " + text);
    }
}
