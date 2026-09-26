package com.furk5nn.videoscreen.client;

import com.furk5nn.videoscreen.block.VideoScreenBlock;
import com.furk5nn.videoscreen.block.VideoScreenBlockEntity;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.blockentity.BlockEntityRenderer;
import net.minecraft.client.renderer.blockentity.BlockEntityRendererProvider;
import net.minecraft.client.renderer.feature.ModelFeatureRenderer;
import net.minecraft.client.renderer.rendertype.RenderType;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.client.renderer.state.level.CameraRenderState;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.core.Direction;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

public final class VideoScreenRenderer implements BlockEntityRenderer<VideoScreenBlockEntity, VideoScreenRenderState> {
    public VideoScreenRenderer(BlockEntityRendererProvider.Context context) {}

    @Override
    public VideoScreenRenderState createRenderState() {
        return new VideoScreenRenderState();
    }

    @Override
    public void extractRenderState(VideoScreenBlockEntity be, VideoScreenRenderState state, float partialTick,
                                   Vec3 camera, ModelFeatureRenderer.@Nullable CrumblingOverlay breakProgress) {
        BlockEntityRenderer.super.extractRenderState(be, state, partialTick, camera, breakProgress);
        state.texture = null;
        if (be.getLevel() == null) return;
        var blockState = be.getBlockState();
        if (!blockState.hasProperty(VideoScreenBlock.FACING)) return;

        PanelLayout panel = PanelLayout.find(be.getLevel(), be.getBlockPos(), blockState);
        ChromiumVideoPlayer player = ClientVideoManager.INSTANCE.playerFor(panel);
        if (player == null || !player.isReady()) return;

        state.texture = player.texture();
        if (state.texture == null) return;
        state.facing = panel.facing();
        state.u0 = (float) panel.x() / panel.width();
        state.u1 = (float) (panel.x() + 1) / panel.width();
        state.v0 = 1.0F - (float) (panel.y() + 1) / panel.height();
        state.v1 = 1.0F - (float) panel.y() / panel.height();
    }

    @Override
    public void submit(VideoScreenRenderState state, PoseStack poseStack, SubmitNodeCollector collector, CameraRenderState camera) {
        if (state.texture == null) return;
        RenderType type = RenderTypes.entityCutout(state.texture);
        collector.submitCustomGeometry(poseStack, type, (pose, buffer) -> emit(
            pose, buffer, state.facing, state.u0, state.v0, state.u1, state.v1
        ));
    }

    private static void emit(PoseStack.Pose pose, VertexConsumer b, Direction f,
                             float u0, float v0, float u1, float v1) {
        final float e = 0.002F;
        switch (f) {
            case NORTH -> quad(b, pose, 0,0,-e, 1,0,-e, 1,1,-e, 0,1,-e, u0,v1,u1,v0, 0,0,-1);
            case SOUTH -> quad(b, pose, 1,0,1+e, 0,0,1+e, 0,1,1+e, 1,1,1+e, u0,v1,u1,v0, 0,0,1);
            case EAST  -> quad(b, pose, 1+e,0,0, 1+e,0,1, 1+e,1,1, 1+e,1,0, u0,v1,u1,v0, 1,0,0);
            case WEST  -> quad(b, pose, -e,0,1, -e,0,0, -e,1,0, -e,1,1, u0,v1,u1,v0, -1,0,0);
            default -> {}
        }
    }

    private static void quad(VertexConsumer b, PoseStack.Pose p,
                             float x0,float y0,float z0, float x1,float y1,float z1,
                             float x2,float y2,float z2, float x3,float y3,float z3,
                             float u0,float v1,float u1,float v0,
                             float nx,float ny,float nz) {
        vertex(b,p,x0,y0,z0,u0,v1,nx,ny,nz);
        vertex(b,p,x1,y1,z1,u1,v1,nx,ny,nz);
        vertex(b,p,x2,y2,z2,u1,v0,nx,ny,nz);
        vertex(b,p,x3,y3,z3,u0,v0,nx,ny,nz);
    }

    private static void vertex(VertexConsumer b, PoseStack.Pose p, float x,float y,float z,
                               float u,float v,float nx,float ny,float nz) {
        b.addVertex(p,x,y,z).setColor(255,255,255,255).setUv(u,v)
            .setOverlay(OverlayTexture.NO_OVERLAY).setLight(0xF000F0).setNormal(p,nx,ny,nz);
    }

    @Override public boolean shouldRenderOffScreen() { return true; }
    @Override public int getViewDistance() { return 128; }
}
