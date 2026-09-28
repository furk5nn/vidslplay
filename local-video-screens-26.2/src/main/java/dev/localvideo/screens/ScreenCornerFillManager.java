package dev.localvideo.screens;

import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.neoforge.network.PacketDistributor;
import net.neoforged.neoforge.event.level.BlockEvent;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

public final class ScreenCornerFillManager {
    private static final int MAX_AREA = 1024;
    private static final Map<UUID, PendingCorner> FIRST = new HashMap<>();
    private static final Map<UUID, PendingPair> AWAITING_CONFIRM = new HashMap<>();

    private ScreenCornerFillManager() {}

    public static void onBlockPlaced(BlockEvent.EntityPlaceEvent event) {
        if (!(event.getEntity() instanceof ServerPlayer player)) return;
        if (!(event.getLevel() instanceof ServerLevel level)) return;
        if (event instanceof BlockEvent.EntityMultiPlaceEvent) return;

        UUID id = player.getUUID();
        BlockState placed = event.getPlacedBlock();

        if (!placed.is(LocalVideoScreens.SCREEN_BLOCK.get())) {
            FIRST.remove(id);
            AWAITING_CONFIRM.remove(id);
            return;
        }

        BlockPos pos = event.getPos().immutable();
        PendingCorner first = FIRST.remove(id);

        if (first == null || first.level() != level) {
            FIRST.put(id, new PendingCorner(level, pos));
            AWAITING_CONFIRM.remove(id);
            return;
        }

        Rectangle rect = rectangle(first.pos(), pos);
        if (rect == null || rect.area() > MAX_AREA || !areaCanBeFilled(level, rect, first.pos(), pos)) {
            // The newest manually placed screen block becomes the next possible first corner.
            FIRST.put(id, new PendingCorner(level, pos));
            AWAITING_CONFIRM.remove(id);
            return;
        }

        PendingPair pair = new PendingPair(level, first.pos(), pos, rect);
        AWAITING_CONFIRM.put(id, pair);

        PacketDistributor.sendToPlayer(player, new ScreenFillNetworking.FillPromptS2C(
                first.pos(), pos, rect.width(), rect.height()
        ));
    }

    public static void confirm(ServerPlayer player, BlockPos a, BlockPos b) {
        UUID id = player.getUUID();
        PendingPair pending = AWAITING_CONFIRM.remove(id);
        FIRST.remove(id);

        if (pending == null) return;
        if (pending.level() != player.level()) return;
        if (!pending.a().equals(a) || !pending.b().equals(b)) return;

        Rectangle rect = rectangle(a, b);
        if (rect == null || rect.area() > MAX_AREA) return;
        if (!areaCanBeFilled(pending.level(), rect, a, b)) {
            player.sendSystemMessage(Component.literal("[Video Screen] Alan artık boş değil."));
            return;
        }

        int placed = 0;
        for (int x = rect.minX(); x <= rect.maxX(); x++) {
            for (int y = rect.minY(); y <= rect.maxY(); y++) {
                for (int z = rect.minZ(); z <= rect.maxZ(); z++) {
                    BlockPos p = new BlockPos(x, y, z);
                    if (p.equals(a) || p.equals(b)) continue;
                    pending.level().setBlockAndUpdate(p, LocalVideoScreens.SCREEN_BLOCK.get().defaultBlockState());
                    placed++;
                }
            }
        }

        player.sendSystemMessage(Component.literal(
                "[Video Screen] " + rect.width() + "x" + rect.height() + " ekran oluşturuldu (" + placed + " blok dolduruldu)."
        ));
    }

    private static boolean areaCanBeFilled(ServerLevel level, Rectangle rect, BlockPos a, BlockPos b) {
        for (int x = rect.minX(); x <= rect.maxX(); x++) {
            for (int y = rect.minY(); y <= rect.maxY(); y++) {
                for (int z = rect.minZ(); z <= rect.maxZ(); z++) {
                    BlockPos p = new BlockPos(x, y, z);
                    if (p.equals(a) || p.equals(b)) continue;
                    BlockState state = level.getBlockState(p);
                    if (!state.isAir()) return false;
                }
            }
        }
        return true;
    }

    private static Rectangle rectangle(BlockPos a, BlockPos b) {
        int dx = a.getX() == b.getX() ? 0 : 1;
        int dy = a.getY() == b.getY() ? 0 : 1;
        int dz = a.getZ() == b.getZ() ? 0 : 1;

        // Exactly two coordinates must vary: two opposite corners on one plane.
        if (dx + dy + dz != 2) return null;

        int minX = Math.min(a.getX(), b.getX());
        int maxX = Math.max(a.getX(), b.getX());
        int minY = Math.min(a.getY(), b.getY());
        int maxY = Math.max(a.getY(), b.getY());
        int minZ = Math.min(a.getZ(), b.getZ());
        int maxZ = Math.max(a.getZ(), b.getZ());

        int width;
        int height;
        if (a.getY() != b.getY()) {
            height = Math.abs(a.getY() - b.getY()) + 1;
            width = (a.getX() != b.getX())
                    ? Math.abs(a.getX() - b.getX()) + 1
                    : Math.abs(a.getZ() - b.getZ()) + 1;
        } else {
            width = Math.abs(a.getX() - b.getX()) + 1;
            height = Math.abs(a.getZ() - b.getZ()) + 1;
        }

        return new Rectangle(minX, maxX, minY, maxY, minZ, maxZ, width, height);
    }

    private record PendingCorner(ServerLevel level, BlockPos pos) {}
    private record PendingPair(ServerLevel level, BlockPos a, BlockPos b, Rectangle rect) {}

    private record Rectangle(
            int minX, int maxX,
            int minY, int maxY,
            int minZ, int maxZ,
            int width, int height
    ) {
        int area() {
            return width * height;
        }
    }
}
