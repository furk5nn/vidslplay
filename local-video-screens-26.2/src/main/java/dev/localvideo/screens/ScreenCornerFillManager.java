package dev.localvideo.screens;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.neoforge.event.level.BlockEvent;
import net.neoforged.neoforge.network.PacketDistributor;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

public final class ScreenCornerFillManager {
    private static final int MAX_WIDTH = 64;
    private static final int MAX_HEIGHT = 64;
    private static final int MAX_AREA = 1024;
    private static final Map<UUID, PendingPlacement> PENDING = new HashMap<>();

    private ScreenCornerFillManager() {}

    public static void onBlockPlaced(BlockEvent.EntityPlaceEvent event) {
        if (!(event.getEntity() instanceof ServerPlayer player)) return;
        if (!(event.getLevel() instanceof ServerLevel level)) return;
        if (event instanceof BlockEvent.EntityMultiPlaceEvent) return;

        UUID id = player.getUUID();
        BlockState placed = event.getPlacedBlock();

        if (!placed.is(LocalVideoScreens.SCREEN_BLOCK.get())) {
            PENDING.remove(id);
            return;
        }

        BlockPos origin = event.getPos().immutable();
        Direction facing = player.getDirection();
        if (!facing.getAxis().isHorizontal()) {
            facing = Direction.NORTH;
        }

        PENDING.put(id, new PendingPlacement(level, origin, facing));
        PacketDistributor.sendToPlayer(player,
                new ScreenFillNetworking.FillPromptS2C(origin, facing.get3DDataValue()));
    }

    public static void confirm(ServerPlayer player, BlockPos origin, int facingId, int width, int height) {
        PendingPlacement pending = PENDING.remove(player.getUUID());
        if (pending == null) return;
        if (pending.level() != player.level()) return;
        if (!pending.origin().equals(origin)) return;
        if (pending.facing().get3DDataValue() != facingId) return;

        if (width < 1 || height < 1
                || width > MAX_WIDTH || height > MAX_HEIGHT
                || width * height > MAX_AREA) {
            player.sendSystemMessage(Component.literal("[Video Screen] Geçersiz ekran ölçüsü."));
            return;
        }

        ServerLevel level = pending.level();
        if (!level.getBlockState(origin).is(LocalVideoScreens.SCREEN_BLOCK.get())) {
            player.sendSystemMessage(Component.literal("[Video Screen] Başlangıç bloğu artık yerinde değil."));
            return;
        }

        Direction right = pending.facing().getClockWise();

        for (int x = 0; x < width; x++) {
            for (int y = 0; y < height; y++) {
                BlockPos p = origin.relative(right, x).above(y);
                if (p.equals(origin)) continue;
                if (!level.getBlockState(p).isAir()) {
                    player.sendSystemMessage(Component.literal(
                            "[Video Screen] " + width + "x" + height + " alan boş değil; hiçbir blok değiştirilmedi."
                    ));
                    return;
                }
            }
        }

        int placed = 0;
        for (int x = 0; x < width; x++) {
            for (int y = 0; y < height; y++) {
                BlockPos p = origin.relative(right, x).above(y);
                if (p.equals(origin)) continue;
                level.setBlockAndUpdate(p, LocalVideoScreens.SCREEN_BLOCK.get().defaultBlockState());
                placed++;
            }
        }

        player.sendSystemMessage(Component.literal(
                "[Video Screen] " + width + "x" + height + " ekran oluşturuldu (" + placed + " blok eklendi)."
        ));
    }

    private record PendingPlacement(ServerLevel level, BlockPos origin, Direction facing) {}
}
