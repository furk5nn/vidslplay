package dev.localvideo.screens.client;

import de.keksuccino.rinku.Rinku;
import de.keksuccino.rinku.RinkuBrowser;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.resources.Identifier;
import net.minecraft.util.LightCoordsUtil;
import net.minecraft.world.phys.Vec3;
import org.cef.browser.CefBrowser;
import org.cef.browser.CefFrame;
import org.cef.handler.CefLoadHandlerAdapter;

import java.io.File;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;

public final class VideoScreenManager {
    private static final VideoScreenManager INSTANCE = new VideoScreenManager();
    private static final int VALIDITY_CHECK_TICKS = 10;
    private static final double MAX_RENDER_DISTANCE_SQ = 128.0 * 128.0;

    private final Map<String, VideoSession> sessions = new HashMap<>();
    private final Map<Integer, VideoSession> byBrowserId = new HashMap<>();
    private boolean loadHandlerInstalled;
    private int tickCounter;

    private VideoScreenManager() {}

    public static VideoScreenManager get() { return INSTANCE; }

    public void play(ScreenGeometry geometry, File file) {
        if (file == null || !file.isFile()) return;

        VideoSession previous = sessions.remove(geometry.key());
        if (previous != null) previous.close();

        VideoCompatibilityCache.prepare(file, compatibleFile -> {
            if (compatibleFile == null || !compatibleFile.isFile()) return;

            Minecraft mc = Minecraft.getInstance();
            if (mc.level == null || !geometry.isStillValid(mc.level)) return;

            VideoSession session = new VideoSession(geometry, compatibleFile);
            sessions.put(geometry.key(), session);
            ensureLoadHandler();
            session.start();
        });
    }

    public boolean openInteraction(net.minecraft.world.level.Level level, net.minecraft.core.BlockPos pos, net.minecraft.core.Direction face) {
        for (VideoSession session : sessions.values()) {
            ScreenGeometry geometry = session.geometry();
            if (!geometry.dimension().equals(level.dimension())) continue;
            if (geometry.face() != face) continue;
            if (!geometry.blocks().contains(pos)) continue;
            if (session.browser() == null) return false;

            Minecraft.getInstance().gui.setScreen(new VideoInteractionScreen(session));
            return true;
        }
        return false;
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
                int id = browser.getIdentifier();
                Minecraft.getInstance().execute(() -> {
                    VideoSession session = byBrowserId.get(id);
                    if (session != null) session.styleVideoDocument();
                });
            }
        });
    }

    void bindBrowser(VideoSession session, RinkuBrowser browser) { byBrowserId.put(browser.getIdentifier(), session); }
    void unbindBrowser(RinkuBrowser browser) { byBrowserId.remove(browser.getIdentifier()); }

    public void clientTick() {
        Minecraft mc = Minecraft.getInstance();
        if (mc.level == null) {
            closeAll();
            return;
        }
        if (++tickCounter < VALIDITY_CHECK_TICKS) return;
        tickCounter = 0;
        var iterator = sessions.entrySet().iterator();
        while (iterator.hasNext()) {
            var entry = iterator.next();
            VideoSession session = entry.getValue();
            if (!session.geometry().isStillValid(mc.level)) {
                iterator.remove();
                session.close();
            }
        }
    }

    public void closeAll() {
        if (sessions.isEmpty()) return;
        for (VideoSession session : new ArrayList<>(sessions.values())) session.close();
        sessions.clear();
        byBrowserId.clear();
    }

    public void submitGeometry(net.neoforged.neoforge.client.event.SubmitCustomGeometryEvent event) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.level == null || sessions.isEmpty()) return;
        Vec3 camera = event.getLevelRenderState().cameraRenderState.pos;
        var stack = event.getPoseStack();
        var collector = event.getSubmitNodeCollector();

        for (VideoSession session : sessions.values()) {
            ScreenGeometry geometry = session.geometry();
            if (!geometry.dimension().equals(mc.level.dimension())) continue;
            Identifier texture = session.texture();
            if (texture == null) continue;

            Vec3 corner = geometry.lowerLeftSurfaceCorner();
            if (corner.distanceToSqr(camera) > MAX_RENDER_DISTANCE_SQ) continue;

            Vec3 r = Vec3.atLowerCornerOf(geometry.right().getUnitVec3i()).scale(geometry.width());
            Vec3 u = Vec3.atLowerCornerOf(geometry.up().getUnitVec3i()).scale(geometry.height());

            stack.pushPose();
            stack.translate(corner.x - camera.x, corner.y - camera.y, corner.z - camera.z);
            collector.submitCustomGeometry(stack, RenderTypes.text(texture), (pose, buffer) -> {
                buffer.addVertex(pose, 0.0F, 0.0F, 0.0F).setColor(-1).setUv(0.0F, 1.0F).setLight(LightCoordsUtil.FULL_BRIGHT);
                buffer.addVertex(pose, (float) r.x, (float) r.y, (float) r.z).setColor(-1).setUv(1.0F, 1.0F).setLight(LightCoordsUtil.FULL_BRIGHT);
                buffer.addVertex(pose, (float) (r.x + u.x), (float) (r.y + u.y), (float) (r.z + u.z)).setColor(-1).setUv(1.0F, 0.0F).setLight(LightCoordsUtil.FULL_BRIGHT);
                buffer.addVertex(pose, (float) u.x, (float) u.y, (float) u.z).setColor(-1).setUv(0.0F, 0.0F).setLight(LightCoordsUtil.FULL_BRIGHT);
            });
            stack.popPose();
        }
    }
}
