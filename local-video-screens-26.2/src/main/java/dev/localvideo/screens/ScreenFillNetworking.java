package dev.localvideo.screens;

import dev.localvideo.screens.client.ScreenFillConfirmScreen;
import net.minecraft.client.Minecraft;
import net.minecraft.core.BlockPos;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.neoforge.client.network.ClientPacketDistributor;
import net.neoforged.neoforge.network.event.RegisterPayloadHandlersEvent;
import net.neoforged.neoforge.network.handling.IPayloadContext;
import net.neoforged.neoforge.network.registration.PayloadRegistrar;

public final class ScreenFillNetworking {
    private static final String VERSION = "1";

    private ScreenFillNetworking() {}

    public static void register(IEventBus modBus) {
        modBus.addListener(ScreenFillNetworking::onRegisterPayloads);
    }

    private static void onRegisterPayloads(RegisterPayloadHandlersEvent event) {
        PayloadRegistrar registrar = event.registrar(VERSION);
        registrar.playToClient(
                FillPromptS2C.TYPE,
                FillPromptS2C.CODEC,
                FillPromptS2C::handle
        );
        registrar.playToServer(
                FillConfirmC2S.TYPE,
                FillConfirmC2S.CODEC,
                FillConfirmC2S::handle
        );
    }

    public static void confirm(BlockPos a, BlockPos b) {
        ClientPacketDistributor.sendToServer(new FillConfirmC2S(a, b));
    }

    public record FillPromptS2C(BlockPos a, BlockPos b, int width, int height) implements CustomPacketPayload {
        public static final Type<FillPromptS2C> TYPE =
                new Type<>(Identifier.fromNamespaceAndPath(LocalVideoScreens.MOD_ID, "fill_prompt"));

        public static final StreamCodec<RegistryFriendlyByteBuf, FillPromptS2C> CODEC = StreamCodec.of(
                (buf, pkt) -> {
                    buf.writeBlockPos(pkt.a());
                    buf.writeBlockPos(pkt.b());
                    buf.writeVarInt(pkt.width());
                    buf.writeVarInt(pkt.height());
                },
                buf -> new FillPromptS2C(
                        buf.readBlockPos(),
                        buf.readBlockPos(),
                        buf.readVarInt(),
                        buf.readVarInt()
                )
        );

        @Override
        public Type<? extends CustomPacketPayload> type() {
            return TYPE;
        }

        private static void handle(FillPromptS2C pkt, IPayloadContext context) {
            context.enqueueWork(() -> Minecraft.getInstance().gui.setScreen(
                    new ScreenFillConfirmScreen(pkt.a(), pkt.b(), pkt.width(), pkt.height())
            ));
        }
    }

    public record FillConfirmC2S(BlockPos a, BlockPos b) implements CustomPacketPayload {
        public static final Type<FillConfirmC2S> TYPE =
                new Type<>(Identifier.fromNamespaceAndPath(LocalVideoScreens.MOD_ID, "fill_confirm"));

        public static final StreamCodec<RegistryFriendlyByteBuf, FillConfirmC2S> CODEC = StreamCodec.of(
                (buf, pkt) -> {
                    buf.writeBlockPos(pkt.a());
                    buf.writeBlockPos(pkt.b());
                },
                buf -> new FillConfirmC2S(buf.readBlockPos(), buf.readBlockPos())
        );

        @Override
        public Type<? extends CustomPacketPayload> type() {
            return TYPE;
        }

        private static void handle(FillConfirmC2S pkt, IPayloadContext context) {
            context.enqueueWork(() -> {
                if (context.player() instanceof ServerPlayer player) {
                    ScreenCornerFillManager.confirm(player, pkt.a(), pkt.b());
                }
            });
        }
    }
}
