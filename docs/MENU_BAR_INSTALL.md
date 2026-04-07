# Menu Bar LaunchAgent Install

The menu bar app can be installed into a stable user-space path and managed by `launchd`, matching the daemon install pattern.

## Files

- install helper: `scripts/install_menu_bar.sh`
- uninstall helper: `scripts/uninstall_menu_bar.sh`
- status helper: `scripts/check_menu_bar.sh`
- template plist: `launchd/com.vmlxstation.menu-bar.plist`

## Behavior

- builds `VmlxStationMenuBar` with `swift build`
- copies the executable to `~/Library/Application Support/vmlx-station/bin/VmlxStationMenuBar`
- writes a stable wrapper at `~/Library/Application Support/vmlx-station/bin/run_vmlx_station_menu_bar.sh`
- installs `~/Library/LaunchAgents/com.vmlxstation.menu-bar.plist`
- starts the LaunchAgent in the user `Aqua` session

## Notes

- default build configuration is `debug`
- override with `BUILD_CONFIGURATION=release ./scripts/install_menu_bar.sh`
- uninstall removes the plist, wrapper, and copied executable, but leaves logs in place
