# Template Capture & Maintenance

Accurate template images are essential for reliable automation. This guide explains how to capture new assets or update existing ones for each subsystem.

## General capture workflow
1. **Prepare RuneLite**
   - Set RuneLite to fixed window mode and ensure the UI scale matches the environment where automation will run.
   - Disable distracting UI overlays so templates remain clean.
2. **Launch a preview**
   - Use `WindowCaptureService.configure_preview()` inside a Python shell or enable preview mode in `AgilitySkill` to open an OpenCV window that mirrors the RuneLite client.【F:automation/window.py†L43-L88】【F:automation/skills/agility.py†L95-L124】
3. **Grab screenshots**
   - Trigger `WindowCaptureService.capture()` to save colour frames. Convert to grayscale if the consumer module expects grayscale templates (e.g. agility, minimap).【F:automation/window.py†L70-L96】
   - Alternatively, use RuneLite's built-in screenshot hotkeys and crop with an image editor.
4. **Crop and normalise**
   - Crop tightly around the feature being matched.
   - Save as PNG for lossless quality unless the original asset already uses JPEG (e.g. some minimap templates).
5. **Validate**
   - Replace the file in the repository, restart the automation script, and confirm matches via log output or on-screen overlays.

## Naming conventions & expected regions
### Minimap / navigation templates (`Agility/Canifis/Map*.jpg`)
- **Prefix:** `Map`
- **Ordering:** Append sequential digits (e.g. `Map1.jpg`, `Map2.jpg`). Ordering controls waypoint creation because `MinimapTemplateReader` sorts numerically.【F:navigation/minimap.py†L42-L77】
- **Region:** Crop the minimap area (top-right of the RuneLite window by default). Maintain consistent zoom and orientation.
- **Recommended size:** Match the RuneLite minimap scale used by your automation environment.

### Agility course interaction templates (`Agility/Canifis/Clk*.png`, `Clm*.png`, `Mog*.png`)
- **Prefixes:**
  - `Clk` for clickable course elements.
  - `Clm` or `Cl` for climb/ladder interactions.
  - `Mog` for marks of grace.
- **Region:** Crop around the in-game hotspot or minimap marker detected in grayscale captures.
- **Notes:** The agility decision engine checks prefixes in priority order (`Map` → `Mog` → `Cl*`), so keep naming consistent to preserve behaviour.【F:automation/skills/agility.py†L62-L109】

### Login flow templates (`Login/*.png`, `Login/*.jpg`)
- **Examples:** `1 Welcome.png`, `LoginField.png`, `PassField.png`, `3 ClickToPlay.jpg`.
- **Region:** Capture the specific UI element (button, text field, etc.) in the RuneLite login screen.
- **Usage:** `Login.py` uses these templates with a `cv2.TM_CCOEFF_NORMED` matcher and a threshold of `0.8` to trigger UI actions.【F:Login.py†L90-L124】

### Inventory/object templates (`perception/templates/*.png`)
- **Naming:** The filename stem becomes the detection label. Use descriptive names such as `noted_herb.png` or `empty_slot.png`.
- **Region:** Crop the inventory cell (including some padding) to avoid false positives.
- **Alpha channel:** Saving with transparency helps focus the match on relevant pixels; OpenCV loads alpha-aware templates in `TemplateInventoryRecognizer` automatically.【F:perception/inventory.py†L42-L55】

## Updating templates safely
1. **Work in a branch** and store raw screenshots separately so you can regenerate templates if needed.
2. **Run the associated automation** (GUI, agility loop, login script) and check log output for messages like "state recognized" or `InventoryDetection` hits to verify the new asset works.【F:automation/skills/agility.py†L114-L136】【F:perception/inventory.py†L56-L96】【F:Login.py†L104-L124】
3. **Version control:** Commit both the updated template and any documentation changes explaining the update rationale.
4. **Share settings:** Document the RuneLite zoom, brightness, or plugin configuration when sharing templates with teammates to avoid mismatches.

## Troubleshooting mismatches
- **No matches found:** Lower the detection threshold slightly (e.g. `TemplateLibrary.threshold` or `TemplateInventoryRecognizer` `detection_threshold`) and retest. Re-capture with better lighting if necessary.【F:automation/templates.py†L17-L56】【F:perception/inventory.py†L34-L53】
- **False positives:** Tighten crops, remove background noise, or increase thresholds.
- **Window drift:** Ensure `WindowCaptureService` manages geometry (`manage_geometry=True`) so captured regions align with stored templates.【F:automation/window.py†L52-L73】
