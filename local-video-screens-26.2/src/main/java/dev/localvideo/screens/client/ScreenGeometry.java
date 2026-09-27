package dev.localvideo.screens.client;

import dev.localvideo.screens.LocalVideoScreens;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayDeque;
import java.util.HashSet;
import java.util.Set;

public record ScreenGeometry(
        ResourceKey<Level> dimension,
        BlockPos origin,
        Direction face,
        Direction right,
        Direction up,
        int width,
        int height,
        Set<BlockPos> blocks
) {
    private static final int MAX_SCREEN_BLOCKS = 1024;

    public static Result discover(Level level, BlockPos clicked, Direction face) {
        if (!isScreen(level, clicked)) {
            return Result.error("Bu blok ekran bloğu değil.");
        }

        Axes axes = Axes.forFace(face);
        Set<BlockPos> component = new HashSet<>();
        ArrayDeque<BlockPos> queue = new ArrayDeque<>();
        component.add(clicked.immutable());
        queue.add(clicked.immutable());

        Direction[] neighbors = {axes.right(), axes.right().getOpposite(), axes.up(), axes.up().getOpposite()};
        while (!queue.isEmpty()) {
            BlockPos pos = queue.removeFirst();
            for (Direction dir : neighbors) {
                BlockPos next = pos.relative(dir);
                if (component.contains(next) || !isScreen(level, next)) {
                    continue;
                }
                if (component.size() >= MAX_SCREEN_BLOCKS) {
                    return Result.error("Ekran en fazla " + MAX_SCREEN_BLOCKS + " blok olabilir.");
                }
                BlockPos immutable = next.immutable();
                component.add(immutable);
                queue.addLast(immutable);
            }
        }

        int minU = Integer.MAX_VALUE, maxU = Integer.MIN_VALUE;
        int minV = Integer.MAX_VALUE, maxV = Integer.MIN_VALUE;
        for (BlockPos pos : component) {
            BlockPos delta = pos.subtract(clicked);
            int u = dot(delta, axes.right());
            int v = dot(delta, axes.up());
            minU = Math.min(minU, u);
            maxU = Math.max(maxU, u);
            minV = Math.min(minV, v);
            maxV = Math.max(maxV, v);
        }

        int width = maxU - minU + 1;
        int height = maxV - minV + 1;
        if ((long) width * height != component.size()) {
            return Result.error("Ekran blokları boşluksuz bir dikdörtgen olmalı.");
        }

        BlockPos origin = clicked.relative(axes.right(), minU).relative(axes.up(), minV).immutable();
        for (int v = 0; v < height; v++) {
            for (int u = 0; u < width; u++) {
                if (!component.contains(origin.relative(axes.right(), u).relative(axes.up(), v))) {
                    return Result.error("Ekran blokları boşluksuz bir dikdörtgen olmalı.");
                }
            }
        }

        return Result.ok(new ScreenGeometry(level.dimension(), origin, face, axes.right(), axes.up(), width, height, Set.copyOf(component)));
    }

    public boolean isStillValid(Level level) {
        if (level == null || !level.dimension().equals(dimension)) {
            return false;
        }
        for (BlockPos pos : blocks) {
            if (!isScreen(level, pos)) {
                return false;
            }
        }
        return true;
    }

    public Vec3 lowerLeftSurfaceCorner() {
        Vec3 center = Vec3.atCenterOf(origin);
        Vec3 n = Vec3.atLowerCornerOf(face.getUnitVec3i());
        Vec3 r = Vec3.atLowerCornerOf(right.getUnitVec3i());
        Vec3 u = Vec3.atLowerCornerOf(up.getUnitVec3i());
        return center.add(n.scale(0.501)).add(r.scale(-0.5)).add(u.scale(-0.5));
    }

    public String key() {
        return dimension.identifier() + ":" + origin.asLong() + ":" + face.getName() + ":" + width + "x" + height;
    }

    private static boolean isScreen(Level level, BlockPos pos) {
        return level.getBlockState(pos).is(LocalVideoScreens.SCREEN_BLOCK.get());
    }

    private static int dot(BlockPos p, Direction axis) {
        var n = axis.getUnitVec3i();
        return p.getX() * n.getX() + p.getY() * n.getY() + p.getZ() * n.getZ();
    }

    private record Axes(Direction right, Direction up) {
        static Axes forFace(Direction face) {
            return switch (face) {
                case NORTH -> new Axes(Direction.WEST, Direction.UP);
                case SOUTH -> new Axes(Direction.EAST, Direction.UP);
                case WEST -> new Axes(Direction.SOUTH, Direction.UP);
                case EAST -> new Axes(Direction.NORTH, Direction.UP);
                case UP -> new Axes(Direction.EAST, Direction.NORTH);
                case DOWN -> new Axes(Direction.EAST, Direction.SOUTH);
            };
        }
    }

    public record Result(ScreenGeometry geometry, String error) {
        static Result ok(ScreenGeometry geometry) { return new Result(geometry, null); }
        static Result error(String error) { return new Result(null, error); }
        public boolean success() { return geometry != null; }
    }
}
