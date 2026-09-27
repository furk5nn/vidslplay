package dev.localvideo.screens.client;

import net.minecraft.client.Camera;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.client.input.MouseButtonEvent;
import net.minecraft.network.chat.Component;
import net.minecraft.world.phys.Vec3;
import org.joml.Matrix4f;
import org.joml.Vector4f;

final class VideoInteractionScreen extends Screen {
    private final VideoSession session;
    private final Matrix4f viewProjection = new Matrix4f();
    private final Matrix4f inverse = new Matrix4f();

    VideoInteractionScreen(VideoSession session) {
        super(Component.empty());
        this.session = session;
    }

    @Override
    public boolean isPauseScreen() {
        return false;
    }

    @Override
    protected void init() {
        super.init();
        if (session.browser() != null) {
            session.browser().setFocus(true);
        }
    }

    @Override
    public void onClose() {
        if (session.browser() != null) {
            session.browser().setFocus(false);
        }
        super.onClose();
    }

    @Override
    public void extractRenderState(GuiGraphicsExtractor guiGraphics, int mouseX, int mouseY, float partialTick) {
        // Intentionally draw no GUI. The world and the in-world browser texture stay visible.
    }

    @Override
    public void mouseMoved(double mouseX, double mouseY) {
        BrowserPoint p = browserPoint(mouseX, mouseY);
        if (p != null && session.browser() != null) {
            session.browser().sendMouseMove(p.x(), p.y());
        }
        super.mouseMoved(mouseX, mouseY);
    }

    @Override
    public boolean mouseClicked(MouseButtonEvent event, boolean isDoubleClick) {
        if (event.button() == 1) {
            onClose();
            return true;
        }

        BrowserPoint p = browserPoint(event.x(), event.y());
        if (p == null || session.browser() == null) {
            return true;
        }

        session.browser().sendMouseMove(p.x(), p.y());
        session.browser().sendMousePress(p.x(), p.y(), event.button());
        session.browser().setFocus(true);
        return true;
    }

    @Override
    public boolean mouseReleased(MouseButtonEvent event) {
        BrowserPoint p = browserPoint(event.x(), event.y());
        if (p != null && session.browser() != null) {
            session.browser().sendMouseMove(p.x(), p.y());
            session.browser().sendMouseRelease(p.x(), p.y(), event.button());
            return true;
        }
        return true;
    }

    @Override
    public boolean mouseScrolled(double mouseX, double mouseY, double scrollX, double scrollY) {
        BrowserPoint p = browserPoint(mouseX, mouseY);
        if (p != null && session.browser() != null) {
            session.browser().sendMouseWheel(p.x(), p.y(), scrollY, 0);
        }
        return true;
    }

    private BrowserPoint browserPoint(double guiMouseX, double guiMouseY) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.level == null || session.browser() == null) return null;

        Camera camera = mc.gameRenderer.mainCamera();
        Vec3 cameraPos = camera.position();

        camera.getViewRotationProjectionMatrix(viewProjection)
                .translate((float) -cameraPos.x, (float) -cameraPos.y, (float) -cameraPos.z)
                .invert(inverse);

        float ndcX = (float) (2.0 * guiMouseX / Math.max(1, width) - 1.0);
        float ndcY = (float) (1.0 - 2.0 * guiMouseY / Math.max(1, height));

        Vec3 a = unproject(ndcX, ndcY, 0.0F);
        Vec3 b = unproject(ndcX, ndcY, 1.0F);
        if (a == null || b == null) return null;

        Vec3 rayOrigin = cameraPos;
        Vec3 rayDir = b.subtract(a).normalize();

        ScreenGeometry g = session.geometry();
        Vec3 corner = g.lowerLeftSurfaceCorner();
        Vec3 normal = Vec3.atLowerCornerOf(g.face().getUnitVec3i());

        double denom = rayDir.dot(normal);
        if (Math.abs(denom) < 1.0e-7) return null;

        double t = corner.subtract(rayOrigin).dot(normal) / denom;
        if (t <= 0.0) return null;

        Vec3 hit = rayOrigin.add(rayDir.scale(t));
        Vec3 local = hit.subtract(corner);

        Vec3 right = Vec3.atLowerCornerOf(g.right().getUnitVec3i());
        Vec3 up = Vec3.atLowerCornerOf(g.up().getUnitVec3i());

        double u = local.dot(right) / g.width();
        double v = local.dot(up) / g.height();
        if (u < 0.0 || u > 1.0 || v < 0.0 || v > 1.0) return null;

        int x = (int) Math.round(u * (session.browserWidth() - 1));
        int y = (int) Math.round((1.0 - v) * (session.browserHeight() - 1));
        x = Math.max(0, Math.min(session.browserWidth() - 1, x));
        y = Math.max(0, Math.min(session.browserHeight() - 1, y));

        return new BrowserPoint(x, y);
    }

    private Vec3 unproject(float x, float y, float z) {
        Vector4f p = new Vector4f(x, y, z, 1.0F).mul(inverse);
        if (Math.abs(p.w) < 1.0e-7F) return null;
        float invW = 1.0F / p.w;
        return new Vec3(p.x * invW, p.y * invW, p.z * invW);
    }

    private record BrowserPoint(int x, int y) {}
}
