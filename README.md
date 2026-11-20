# Cosmic Sky (Fabric, Minecraft 26.3, bez Fabric API)

Dzień: **Saturn** · Noc: **czarna dziura** · End: **Droga Mleczna**

## Instalacja
1. Minecraft 26.3, Fabric Loader >= 0.19.5, Java 25 (bez Fabric API).
2. Wrzuć `cosmic-sky-*.jar` do `mods/` i uruchom grę (mod skopiuje pack do `resourcepacks/`).
3. Opcje -> Paczki zasobów -> włącz **cosmic_sky_pack.zip**.

`cosmic_sky_pack.zip` działa też samodzielnie jako zwykły resource pack.

## Struktura (płaska, wszystko w katalogu głównym)
- `CosmicSkyMod.java` – kod moda (kopiuje pack do resourcepacks)
- `fabric.mod.json`, `icon.png`, `cosmic_sky_pack.zip` – zasoby moda
- `build.gradle`, `settings.gradle`, `gradle.properties` – build
- `build.yml` – workflow GitHub Actions (patrz niżej)
- `generate_textures.py` – generator tekstur (pillow, numpy)

## Build na GitHubie
GitHub wymaga, by workflow leżał w `.github/workflows/`. Na stronie repo kliknij
`build.yml` -> ikona ołówka -> w polu nazwy wpisz `.github/workflows/build.yml`
(slashe tworzą foldery) -> Commit. Potem zakładka **Actions** buduje jar
(artefakt `cosmic-sky`).

## Build lokalnie
`gradle build` (Gradle 9.5.1, JDK 25) -> `build/libs/`.
