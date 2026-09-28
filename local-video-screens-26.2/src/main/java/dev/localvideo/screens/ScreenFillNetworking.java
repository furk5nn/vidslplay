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
    private static final String VERSION = "2";

    private ScreenFillNetworking() {}

    public static void register(IEventBus modBus) {
        modBus.addListener(ScreenFillNetworking::onRegisterPayloads);
    }

    private static void onRegisterPayloads(RegisterPayloadHandlersEvent event) {
        PayloadRegistrar registrar = event.registrar(VERSION);
        registrar.playToClient(FillPromptS2C.TYPE, FillPromptS2C.CODEC, FillPromptS2C::handle);
        registrar.playToServer(FillConfirmC2S.TYPE, FillConfirmC2S.CODEC, FillConfirmC2S::handle);
    }

    public static void confirm(BlockPos origin, int facingId, int width, int height) {
        ClientPacketDistributor.sendToServer(new FillConfirmC2S(origin, facingId, width, height));
    }

    public record FillPromptS2C(BlockPos origin, int facingId) implements CustomPacketPayload {
        public static final Type<FillPromptS2C> TYPE =
                new Type<>(Identifier.fromNamespaceAndPath(LocalVideoScreens.MOD_ID, "fill_prompt"));

        public static final StreamCodec<RegistryFriendlyByteBuf, FillPromptS2C> CODEC = StreamCodec.of(
                (buf, pkt) -> {
                    buf.writeBlockPos(pkt.origin());
                    buf.writeVarInt(pkt.facingId());
                },
                buf -> new FillPromptS2C(buf.readBlockPos(), buf.readVarInt())
        );

        @Override
        public Type<? extends CustomPacketPayload> type() {
            return TYPE;
        }

        private static void handle(FillPromptS2C pkt, IPayloadContext context) {
            context.enqueueWork(() -> Minecraft.getInstance().gui.setScreen(
                    new ScreenFillConfirmScreen(pkt.origin(), pkt.facingId())
            ));
        }
    }

    public record FillConfirmC2S(BlockPos origin, int facingId, int width, int height)
            implements CustomPacketPayload {
        public static final Type<FillConfirmC2S> TYPE =
                new Type<>(Identifier.fromNamespaceAndPath(LocalVideoScreens.MOD_ID, "fill_confirm"));

        public static final StreamCodec<RegistryFriendlyByteBuf, FillConfirmC2S> CODEC = StreamCodec.of(
                (buf, pkt) -> {
                    buf.writeBlockPos(pkt.origin());
                    buf.writeVarInt(pkt.facingId());
                    buf.writeVarInt(pkt.width());
                    buf.writeVarInt(pkt.height());
                },
                buf -> new FillConfirmC2S(
                        buf.readBlockPos(),
                        buf.readVarInt(),
                        buf.readVarInt(),
                        buf.readVarInt()
                )
        );

        @Override
        public Type<? extends CustomPacketPayload> type() {
            return TYPE;
        }

        private static void handle(FillConfirmC2S pkt, IPayloadContext context) {
            context.enqueueWork(() -> {
                if (context.player() instanceof ServerPlayer player) {
                    ScreenCornerFillManager.confirm(
                            player, pkt.origin(), pkt.facingId(), pkt.width(), pkt.height()
                    );
                }
            });
        }
    }
}
