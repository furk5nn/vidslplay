package com.furk5nn.videoscreen.block;

import com.furk5nn.videoscreen.client.ClientVideoManager;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.EntityBlock;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.block.state.properties.EnumProperty;
import net.minecraft.world.phys.BlockHitResult;
import org.jspecify.annotations.Nullable;

public final class VideoScreenBlock extends Block implements EntityBlock {
    public static final EnumProperty<Direction> FACING = BlockStateProperties.HORIZONTAL_FACING;

    public VideoScreenBlock(Properties properties) {
        super(properties);
        registerDefaultState(stateDefinition.any().setValue(FACING, Direction.NORTH));
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        builder.add(FACING);
    }

    @Override
    public @Nullable BlockState getStateForPlacement(BlockPlaceContext context) {
        Level level = context.getLevel();
        BlockPos pos = context.getClickedPos();

        for (Direction dir : Direction.values()) {
            BlockState neighbor = level.getBlockState(pos.relative(dir));
            if (neighbor.getBlock() instanceof VideoScreenBlock && neighbor.hasProperty(FACING)) {
                return defaultBlockState().setValue(FACING, neighbor.getValue(FACING));
            }
        }

        return defaultBlockState().setValue(FACING, context.getHorizontalDirection().getOpposite());
    }

    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new VideoScreenBlockEntity(pos, state);
    }

    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
        if (!player.isShiftKeyDown()) {
            return InteractionResult.PASS;
        }

        if (level.isClientSide()) {
            ClientVideoManager.INSTANCE.openConfig(level, pos, state);
            return InteractionResult.SUCCESS.withoutItem();
        }

        return InteractionResult.SUCCESS_SERVER.withoutItem();
    }
}
