package com.furk5nn.videoscreen.client;

import net.minecraft.client.renderer.blockentity.state.BlockEntityRenderState;
import net.minecraft.core.Direction;
import net.minecraft.resources.Identifier;

public final class VideoScreenRenderState extends BlockEntityRenderState {
    Identifier texture;
    Direction facing = Direction.NORTH;
    float u0, v0, u1, v1;
}
