package com.furk5nn.videoscreen.client;

import java.io.File;
import java.util.HashMap;
import java.util.Map;
import net.minecraft.client.Minecraft;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import org.cef.browser.CefBrowser;
import org.cef.browser.CefFrame;
import org.cef.handler.CefLoadHandlerAdapter;
import org.lwjgl.util.tinyfd.TinyFileDialogs;
import de.keksuccino.rinku.Rinku;

public final class ClientVideoManager {
    public static final ClientVideoManager INSTANCE = new ClientVideoManager();

    private final Map<Long, WaterMediaVideoPlayer> players = new HashMap<>();
    private boolean loadHandlerInstalled;

    private ClientVideoManager() {}

    public void openConfig(Level level, BlockPos pos, BlockState state) {
        PanelLayout panel = PanelLayout.find(level, pos, state);
        Minecraft.getInstance().gui.setScreen(new VideoSelectScreen(panel));
    }

    public void chooseVideo(PanelLayout panel) {
        String selected = TinyFileDialogs.tinyfd_openFileDialog(
            "Choose local video",
            "",
            null,
            "Video files",
            false
        );
        if (selected == null || selected.isBlank()) return;

        File file = new File(selected);
        if (!file.isFile()) {
            message("Could not open selected file");
            return;
        }

        try {
            long key = panel.root().asLong();
            WaterMediaVideoPlayer old = players.remove(key);
            if (old != null) old.close();

            ensureLoadHandler();

            WaterMediaVideoPlayer player = new WaterMediaVideoPlayer(file, panel.width(), panel.height());
            players.put(key, player);
            player.tickInit();
            message("Loaded: " + file.getName());
        } catch (Throwable e) {
            e.printStackTrace();
            message("Could not open video: " + e.getMessage());
        }
    }

    public WaterMediaVideoPlayer playerFor(PanelLayout panel) {
        WaterMediaVideoPlayer player = players.get(panel.root().asLong());
        if (player != null) {
            player.tickInit();
            if (!panelStillValid(panel)) {
                players.remove(panel.root().asLong());
                player.close();
                return null;
            }
        }
        return player;
    }

    private boolean panelStillValid(PanelLayout panel) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.level == null) return false;
        BlockState root = mc.level.getBlockState(panel.root());
        if (!(root.getBlock() instanceof com.furk5nn.videoscreen.block.VideoScreenBlock)) return false;

        var right = panel.facing().getClockWise();
        for (int y = 0; y < panel.height(); y++) {
            for (int x = 0; x < panel.width(); x++) {
                BlockPos p = panel.root().relative(right, x).above(y);
                BlockState s = mc.level.getBlockState(p);
                if (!(s.getBlock() instanceof com.furk5nn.videoscreen.block.VideoScreenBlock)) return false;
            }
        }
        return true;
    }

    private void ensureLoadHandler() {
        if (loadHandlerInstalled) return;
        if (!Rinku.isInitialized()) {
            Rinku.scheduleForInit(success -> Minecraft.getInstance().execute(() -> {
                if (success) installLoadHandlerNow();
            }));
            return;
        }
        installLoadHandlerNow();
    }

    private void installLoadHandlerNow() {
        if (loadHandlerInstalled || !Rinku.isInitialized()) return;
        loadHandlerInstalled = true;
        Rinku.getClient().addLoadHandler(new CefLoadHandlerAdapter() {
            @Override
            public void onLoadEnd(CefBrowser browser, CefFrame frame, int httpStatusCode) {
                if (browser == null || frame == null || !frame.isMain()) return;
                Minecraft.getInstance().execute(() -> {
                    for (WaterMediaVideoPlayer player : players.values()) {
                        if (player.browser() != null && player.browser().getIdentifier() == browser.getIdentifier()) {
                            player.styleVideoDocument();
                            break;
                        }
                    }
                });
            }
        });
    }

    private static void message(String text) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.player != null) {
            mc.player.displayClientMessage(Component.literal(text), true);
        }
        System.out.println("[VideoScreen] " + text);
    }
}
