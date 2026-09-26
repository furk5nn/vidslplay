package com.furk5nn.videoscreen.block;

import com.furk5nn.videoscreen.registry.ModBlockEntities;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;

public final class VideoScreenBlockEntity extends BlockEntity {
    public VideoScreenBlockEntity(BlockPos pos, BlockState state) {
        super(ModBlockEntities.VIDEO_SCREEN.get(), pos, state);
    }
}
