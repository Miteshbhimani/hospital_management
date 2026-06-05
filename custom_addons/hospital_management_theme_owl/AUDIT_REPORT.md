# Odoo 18 Hospital Management Theme OWL — Technical Audit & Stabilization Report

**Module:** `hospital_management_theme_owl`  
**Audited input version:** `18.0.1.0.11`  
**Stabilized version:** `18.0.1.0.14`  
**Audit date:** 2026-06-05  
**Scope:** The complete uploaded theme addon, including manifest, inherited form/kanban views, OWL/QWeb templates, JavaScript, SCSS, portal styling, assets, and documentation.

## 1. Executive Summary

The reported OWL runtime crash was reproduced by static code tracing and isolated to one legacy kanban helper call inside a modern Odoo 18 kanban card template:

- **Exact original file:** `views/hospital_kanban_detail_views.xml`
- **Exact original line:** 32
- **Original expression:** `kanban_image('res.partner', 'avatar_128', record.id.raw_value)`
- **Failure:** `TypeError: ctx.kanban_image is not a function`

The card uses Odoo 18's modern `<t t-name="card">` template. In Odoo 18, `kanban_image` is injected into the rendering context only for a legacy kanban architecture. Odoo's own source marks the helper as deprecated and directs developers to use an image field widget instead. Therefore, the modern card receives no callable named `kanban_image`, and OWL fails when rendering the patient card.

The module has been patched to use the native Odoo 18 image field widget, and additional compatibility, performance, responsive-layout, accessibility, and CSS-scope issues were corrected. No Python business model, security rule, database schema, or hospital workflow was changed.

## 2. Root Cause Analysis

### 2.1 Exact failing code — before

```xml
<t t-name="card">
    <div class="hmo-kanban-card oe_kanban_global_click">
        <div class="hmo-kanban-avatar">
            <img alt="Patient Avatar"
                 t-att-src="kanban_image('res.partner', 'avatar_128', record.id.raw_value)"/>
        </div>
        ...
    </div>
</t>
```

### 2.2 Why `ctx.kanban_image` is unavailable

Odoo 18 differentiates between:

- legacy kanban templates: `t-name="kanban-box"`
- modern kanban templates: `t-name="card"`

The uploaded view uses the modern `card` template. In Odoo 18's `KanbanRecord.renderingContext`, `kanban_image` is added only when `archInfo.isLegacyArch` is true. The Odoo source explicitly labels the helper deprecated and recommends `<field name="" widget="image"/>`.

This is a **partial legacy-to-modern migration defect**: the outer template was migrated to the modern `card` syntax, but the image rendering expression remained from the legacy kanban API.

### 2.3 Correct Odoo 18 implementation — after

```xml
<field name="avatar_128"/>
...
<div class="hmo-kanban-avatar">
    <field name="avatar_128" widget="image" class="hmo-kanban-avatar-image"/>
</div>
```

The stabilized implementation:

1. declares `avatar_128` in the kanban architecture;
2. renders it through Odoo's native image field widget;
3. preserves the existing avatar size, border radius, and design through scoped SCSS;
4. removes the unavailable legacy helper from executable code.

## 3. Implemented Fixes

| Severity | Area | File | Finding | Implemented correction |
|---|---|---|---|---|
| Critical | Kanban / OWL runtime | `views/hospital_kanban_detail_views.xml` | Modern `card` called legacy-only `kanban_image()` | Replaced with `<field name="avatar_128" widget="image"/>` and declared the field |
| Major | Kanban compatibility | `views/hospital_kanban_detail_views.xml` | Used obsolete/ignored `quick_add="False"` | Replaced with Odoo 18 `quick_create="false"` |
| Moderate | Icon compatibility | `views/hospital_kanban_detail_views.xml` | Used FontAwesome 5-only `fa-procedures` | Replaced with FontAwesome 4-compatible `fa-user` |
| Major | Frontend performance | `static/src/js/theme_detector.js` | MutationObserver ran full DOM queries for every class/name mutation across the entire body | Debounced updates with `requestAnimationFrame` and reduced observation to child-list changes |
| Moderate | Detection reliability | `static/src/js/theme_detector.js` | Only the first matching navbar node was inspected | Checks all relevant navbar nodes |
| Moderate | Browser stability | `static/src/js/quick_panel.js` | Direct `localStorage` access could throw in restricted/privacy contexts | Added safe read/write helpers |
| Minor | Console cleanliness | `static/src/js/quick_panel.js` | Quick-action failures emitted a console warning in addition to a user notification | Retained user notification and removed unnecessary console noise |
| Moderate | CSS compatibility | `static/src/scss/hospital_backend_theme.scss`, `hospital_portal_theme.scss` | Relied on `:has()` selectors | Replaced with explicit state/direct descendant selectors |
| Major | Kanban layout | `static/src/scss/hospital_backend_theme.scss` | Broad `> *` sizing could resize kanban controls/load-more elements | Restricted sizing to records and quick-create cards only |
| Major | List responsiveness | `static/src/scss/hospital_backend_theme.scss` | `.o_list_renderer { overflow: hidden; }` could clip wide tables and prevent horizontal review | Changed renderer to `overflow: auto`; kept visual card styling |
| Moderate | Mobile behavior | `static/src/scss/hospital_backend_theme.scss` | Forced sticky mobile control panel could conflict with Odoo's native responsive header | Removed custom sticky positioning |
| Moderate | Dialog/wizard isolation | `static/src/scss/hospital_backend_theme.scss` | Full-screen form styling could also affect modal forms | Scoped form-sheet geometry to `.o_action_manager .o_form_view` |
| Moderate | Global CSS scope | `static/src/scss/hospital_backend_theme.scss` | Generic `.hm-dashboard` styling was unscoped | Scoped to `body.o_hmo_hospital_active .hm-dashboard` |
| Minor | Image widget layout | `static/src/scss/hospital_backend_theme.scss` | Native image widget wrapper needed explicit full-size layout | Added scoped wrapper sizing within `.hmo-kanban-avatar` |
| Minor | Accessibility | `static/src/xml/hospital_theme_components.xml` | Density toggle and opened quick-action region lacked explicit accessible labels | Added `aria-label`, `title`, and region semantics |
| Minor | Packaging/documentation | `__manifest__.py`, `README.rst` | Documentation incorrectly claimed no database view inheritance | Corrected documentation and bumped module version |
| Minor | Packaging | module root | Python cache files were included | Removed `__pycache__`/`.pyc` from distributable addon |

## 4. Odoo 18 Compatibility Audit

### 4.1 OWL and JavaScript

**Compatible patterns retained**

- ES module marker: `/** @odoo-module **/`
- OWL imports from `@odoo/owl`
- Odoo registry import from `@web/core/registry`
- service injection through `useService` from `@web/core/utils/hooks`
- main-component registration through `registry.category("main_components")`
- action and notification services

**No deprecated legacy JavaScript patterns found**

- no `odoo.define(...)`
- no CommonJS `require(...)`
- no legacy `web.core` import
- no legacy kanban renderer extension
- no component patching or unsupported lifecycle hooks

### 4.2 Kanban architecture

- Modern `t-name="card"` templates are retained.
- Legacy `kanban_image()` was removed from executable code.
- Legacy `kanban-box` is not present.
- `quick_create` is now used instead of `quick_add`.
- Patient image rendering uses the Odoo field widget.

**Residual integration dependency:** Both inherited views replace the complete `<kanban>` root. This is valid XML and preserves the theme's existing card design, but it means future changes to root-level attributes in the base views will not be inherited automatically. Refactoring this without the exact deployed base view architecture could cause a regression, so it was intentionally not changed in this stabilization pass. Validate those two base views during every base-module upgrade.

### 4.3 Static QWeb dashboard inheritance

The following inherited template names and XPath targets are syntactically valid:

- `ReceptionDashboard`
- `DoctorDashboard`
- `LabDashboard`
- `PharmacyDashboard`
- first descendant with class `hm-hero`

Their runtime existence depends on the installed `base_hospital_management` version. The uploaded ZIP did not contain the dependency source, so exact target availability must be confirmed during the Odoo module-upgrade smoke test.

### 4.4 Asset bundles

- All manifest-declared assets exist.
- Variable SCSS loads before backend SCSS.
- OWL/QWeb templates load before the JavaScript components that reference them.
- Portal styling is isolated to `web.assets_frontend`.
- No missing asset reference was found.

## 5. UI/UX Audit

### 5.1 Form views

**Validated/fixed**

- Label hierarchy, field controls, groups, notebooks, statusbars, stat buttons, avatars, and chatter use scoped hospital styles.
- Full-screen form geometry is now scoped under `.o_action_manager`, preventing the same wide-sheet rules from affecting modal wizards/dialogs.
- Mobile form width and title behavior remain responsive.

**Live visual validation required**

- longest labels in translated languages;
- unusually large button boxes;
- side-chatter versus bottom-chatter behavior on the deployed Odoo configuration;
- custom base-module forms that intentionally omit a form sheet.

### 5.2 List views

**Validated/fixed**

- The renderer no longer hides horizontal overflow.
- Headers, hover states, badges, table surface, and rounded container styling remain consistent.
- No custom list XML or field order was changed.

### 5.3 Kanban views

**Validated/fixed**

- Patient card image crash resolved.
- Blood-bank quick-create attribute corrected.
- Unsupported icon replaced.
- Card sizing no longer affects arbitrary renderer children.
- Mobile cards switch to full width.
- Image wrapper and image itself fill the existing 72px avatar container.

### 5.4 Search views and control panel

- Search styling is minimal and scoped.
- The custom mobile sticky control-panel override was removed so Odoo controls native responsive behavior.
- No search-domain/filter logic was altered.

### 5.5 Dashboards

- Existing dashboard branding, palette, layouts, action cards, and pulse strips are preserved.
- `.hm-dashboard` styling is now active only while the hospital theme body-state class is active.
- The floating quick-action panel is hidden on dashboards through an explicit body-state class rather than expensive `:has()` selectors.

### 5.6 Dialogs and wizards

- The module defines no custom dialog or wizard view.
- Full-screen form layout rules are now excluded from modal forms by `.o_action_manager` scoping.
- Existing base-module wizard business behavior remains untouched.

## 6. CSS/SCSS Conflict Audit

### Scoping status

- General backend overrides are under `body.o_hmo_hospital_active`.
- Dashboard generic class styling is now also under the hospital body-state class.
- Portal selectors target known patient/booking/prescription/test/vaccine containers.
- Custom component selectors use the `hmo-` prefix.

### `!important` usage

Seventeen `!important` declarations remain. They are targeted and scoped to the hospital body/dashboard/component selectors, primarily to override Odoo/Bootstrap state styling. No unscoped generic `!important` declaration remains. Removing them without browser-level cascade testing could reintroduce the alignment/color defects this module was created to fix.

### Conflicts corrected

- removed `:has()` dependency;
- removed broad kanban direct-child selector;
- restored list horizontal scrolling;
- removed custom mobile control-panel stickiness;
- isolated full-screen form styling from modal forms;
- scoped the generic dashboard class.

## 7. Performance Audit

### Original concern

The original MutationObserver watched the entire body subtree for child-list and attribute changes and synchronously performed multiple whole-document queries on every matching mutation. OWL renders and animations can generate many class mutations, so this could cause avoidable repeated work.

### Stabilized behavior

- MutationObserver now watches DOM structure changes only.
- Updates are coalesced to at most one check per animation frame.
- Hash changes still trigger theme-state evaluation.
- No additional event listeners are created per render.
- No business RPC or model operation was added.

## 8. Regression Impact Report

### Confirmed untouched

- Python models and methods
- database schema
- security groups, ACLs, and record rules
- menus and action definitions
- domains, contexts, and workflow transitions
- base module source files
- dashboard business data and service calls

### Preserved design language

- existing blue/teal palette
- existing typography stack
- existing rounded-card visual system
- current dashboard/card layouts
- quick-action component and existing actions
- patient and blood-bank detail-card information hierarchy

### Runtime integration items requiring deployment validation

- existence of the two base view XML IDs;
- existence of four dashboard QWeb template names and their `hm-hero` targets;
- existence/accessibility of eight quick-action XML IDs;
- Odoo SCSS bundle compilation in the deployed server environment;
- visual smoke testing with real records and permissions.

## 9. Static Validation Results

| Check | Result |
|---|---|
| Python/manifest syntax | PASS |
| Manifest version and structure | PASS |
| Every manifest asset path exists | PASS |
| XML/QWeb well-formedness | PASS |
| XPath expression syntax | PASS |
| JavaScript syntax (`node --check`) | PASS |
| Executable `kanban_image()` usage | PASS — none remains |
| `quick_add` usage | PASS — none remains |
| legacy `kanban-box` usage | PASS — none remains |
| FontAwesome 5-only `fa-procedures` usage | PASS — none remains |
| SCSS `:has()` usage | PASS — none remains |
| Included Python cache files | PASS — removed |
| Live Odoo module upgrade/install | NOT EXECUTED — deployed Odoo server and dependency source were not included |
| Odoo asset-bundle SCSS compilation | NOT EXECUTED — Odoo/Sass compiler not available in the audit sandbox |
| Browser/permission/responsive smoke test | NOT EXECUTED — requires the running hospital database |

## 10. Deployment and Final Validation Checklist

### Upgrade command

```bash
./odoo-bin -d <database_name> -u hospital_management_theme_owl --stop-after-init
```

Then restart Odoo and hard-refresh the browser. For diagnosis, validate once with `?debug=assets`.

### Required smoke tests

1. Open Patient kanban and confirm all cards render without `ctx.kanban_image` or Owl lifecycle errors.
2. Confirm patient avatars render, including records without a custom avatar.
3. Open Blood Bank kanban and confirm grouping, badge decorations, donor, receiver, and date render correctly.
4. Confirm blood-bank quick creation is disabled as intended.
5. Open Reception, Doctor, Laboratory, and Pharmacy dashboards; confirm inherited pulse blocks render once.
6. Open every quick action using users with relevant roles; confirm missing-access errors appear as notifications only.
7. Validate wide list views can scroll horizontally.
8. Validate forms, notebook tabs, statusbars, stat buttons, chatter, and modal wizards on desktop and tablet widths.
9. Confirm no browser console error and no server traceback.
10. Confirm normal mode and `debug=assets` mode both load successfully.

## 11. Official Technical References

- Odoo 18 kanban record rendering source: https://github.com/odoo/odoo/blob/18.0/addons/web/static/src/views/kanban/kanban_record.js
- Odoo 18 kanban architecture parser: https://github.com/odoo/odoo/blob/18.0/addons/web/static/src/views/kanban/kanban_arch_parser.js
- Odoo 18 view architectures: https://www.odoo.com/documentation/18.0/developer/reference/user_interface/view_architectures.html
- Odoo 18 assets: https://www.odoo.com/documentation/18.0/developer/reference/frontend/assets.html
- Odoo 18 Owl components: https://www.odoo.com/documentation/18.0/developer/reference/frontend/owl_components.html
- Odoo 18 UI icons: https://www.odoo.com/documentation/18.0/developer/reference/user_interface/icons.html


## 10. Follow-up Kanban Rendering Fix — 18.0.1.0.13

A live screenshot showed one valid patient card plus multiple empty white cards. The patient kanban root still used `sample="1"`, so Odoo generated demonstration/sample records. Because those sample records had no meaningful hospital field values, the custom card body rendered empty; the generic kanban wrapper styling then made each empty record visible as a white rounded rectangle.

Implemented corrections:

- removed `sample="1"` from the patient kanban;
- set `quick_create="false"` to avoid inline placeholder creation on this clinical card view;
- reset the structural `.o_kanban_record` wrapper only inside `.o_hmo_detail_kanban`;
- preserved all visual styling and hover behavior on `.hmo-kanban-card`;
- retained patient/blood-bank data, actions, workflows, and existing design language.


## 11. Follow-up Patient Form Alignment Fix — 18.0.1.0.14

A live patient-form screenshot showed the Emergency Contact group and later enterprise-profile fields wrapping below the left column while the right side of the form remained unused. The base enterprise profile already defines Acquisition/Identity and Emergency Contact as two sibling inner groups. The theme-level `.o_group { column-gap: 2rem; }` was added on top of Odoo's native 50% column widths, so two columns plus the extra gap exceeded the row width and forced the second group onto the next line.

Implemented corrections:

- removed the horizontal `column-gap` override and retained Odoo's native responsive group gutters;
- kept the theme's vertical spacing without changing Odoo form geometry;
- inherited only the Enterprise Patient Profile view and converted the standalone Clinical Summary group into two responsive inner groups;
- preserved every field, placeholder, notebook, model, action, access rule, and workflow.


## 12. Follow-up Staff Kanban Avatar Fix — 18.0.1.0.15

A live Staff screenshot showed the normal employee image at the upper-left and an oversized second avatar beside the activity clock. The Staff action was rendering Odoo's standard HR employee kanban. That standard card intentionally includes a compact linked-user avatar next to the activity widget. The theme's broad ``.o_kanban_record img`` rule then overrode the avatar image's native width and height with ``auto`` and allowed it to expand up to 72px, making it look like a duplicate staff image.

Implemented corrections:

- restored native geometry for Odoo inline ``.o_m2o_avatar`` images inside hospital kanbans;
- hid only the redundant linked-user avatar in the hospital Staff kanban footer;
- preserved the primary employee image, presence indicator, activity icon, role grouping, contact details, actions, domains, permissions, and workflows;
- did not modify the Staff Access addon, HR module, or any business logic.
