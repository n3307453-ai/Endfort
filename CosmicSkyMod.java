package pl.cosmicsky;

import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.loader.api.FabricLoader;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.Arrays;

/**
 * Cosmic Sky - bez Fabric API i bez mixinow.
 * <p>
 * Fabric bez Fabric API nie laduje assetow z jara moda, wiec mod przy starcie
 * kopiuje wbudowany resource pack do folderu {@code resourcepacks/}.
 * Wystarczy wlaczyc pack "cosmic_sky_pack.zip" (Opcje -> Paczki zasobow).
 * <p>
 * Dzien: Saturn (slonce), noc: czarna dziura (ksiezyc), End: Droga Mleczna.
 */
public final class CosmicSkyMod implements ClientModInitializer {
    public static final String MOD_ID = "cosmicsky";
    private static final Logger LOG = LoggerFactory.getLogger(MOD_ID);
    private static final String PACK_NAME = "cosmic_sky_pack.zip";

    @Override
    public void onInitializeClient() {
        Path target = FabricLoader.getInstance().getGameDir().resolve("resourcepacks").resolve(PACK_NAME);
        try (InputStream in = CosmicSkyMod.class.getResourceAsStream("/" + PACK_NAME)) {
            if (in == null) {
                LOG.error("Brak wbudowanego packa /{} w jarze moda!", PACK_NAME);
                return;
            }
            byte[] bundled = in.readAllBytes();
            Files.createDirectories(target.getParent());
            if (Files.exists(target) && Arrays.equals(Files.readAllBytes(target), bundled)) {
                LOG.info("Pack {} jest aktualny.", PACK_NAME);
                return;
            }
            Path tmp = target.resolveSibling(PACK_NAME + ".tmp");
            Files.write(tmp, bundled);
            Files.move(tmp, target, StandardCopyOption.REPLACE_EXISTING);
            LOG.info("Zainstalowano {} -> wlacz go w Opcje -> Paczki zasobow.", target);
        } catch (IOException e) {
            LOG.error("Nie udalo sie zainstalowac packa {}", PACK_NAME, e);
        }
    }
}
