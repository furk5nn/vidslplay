package com.furk5nn.videoscreen.client;

import com.furk5nn.videoscreen.block.VideoScreenBlock;
import com.furk5nn.videoscreen.registry.ModBlocks;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;

public record PanelLayout(BlockPos root, int width, int height, int x, int y, Direction facing) {
    private static final int MAX = 64;

    public static PanelLayout find(Level level, BlockPos pos, BlockState state) {
        Direction facing = state.getValue(VideoScreenBlock.FACING);
        Direction right = facing.getClockWise();

        BlockPos left = pos;
        int leftCount = 0;
        while (leftCount < MAX && same(level, left.relative(right.getOpposite()), facing)) {
            left = left.relative(right.getOpposite());
            leftCount++;
        }

        BlockPos bottomLeft = left;
        int down = 0;
        while (down < MAX && same(level, bottomLeft.below(), facing)) {
            bottomLeft = bottomLeft.below();
            down++;
        }

        int width = 1;
        while (width < MAX && same(level, bottomLeft.relative(right, width), facing)) width++;

        int height = 1;
        while (height < MAX && same(level, bottomLeft.above(height), facing)) height++;

        int x = 0;
        BlockPos cursor = bottomLeft;
        while (x < MAX && !cursor.atY(pos.getY()).equals(pos)) {
            cursor = cursor.relative(right);
            x++;
            if (cursor.getY() != pos.getY()) break;
        }
        // Coordinate calculation without relying on axis sign.
        x = Math.abs((pos.getX() - bottomLeft.getX()) * right.getStepX()
                   + (pos.getZ() - bottomLeft.getZ()) * right.getStepZ());
        int y = pos.getY() - bottomLeft.getY();

        return new PanelLayout(bottomLeft.immutable(), width, height, x, y, facing);
    }

    private static boolean same(Level level, BlockPos pos, Direction facing) {
        BlockState s = level.getBlockState(pos);
        return s.is(ModBlocks.VIDEO_SCREEN.get())
            && s.hasProperty(VideoScreenBlock.FACING)
            && s.getValue(VideoScreenBlock.FACING) == facing;
    }
}
