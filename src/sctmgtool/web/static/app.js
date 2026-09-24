// SPDX-License-Identifier: MIT
// Copyright (c) 2026 Łukasz Gieryk

document.addEventListener("DOMContentLoaded", async () => {
  const MAX_SHARE_FRAGMENT_LENGTH = 2048;
  const MAX_RESULT_KEY_LENGTH = 512;
  const apiBaseUrl = (window.SCTMGTOOL_API_BASE_URL || window.location.origin).replace(/\/$/, "");
  const apiUrl = (path) => `${apiBaseUrl}${path}`;
  const attackerSelect = document.querySelector("#attacker-select");
  const defenderSelect = document.querySelector("#defender-select");
  const swapButton = document.querySelector("#swap-units");
  const attackerSummary = document.querySelector("#attacker-summary");
  const defenderSummary = document.querySelector("#defender-summary");
  const attackerWeapons = document.querySelector("#attacker-weapons");
  const attackerUpgrades = document.querySelector("#attacker-upgrades");
  const defenderUpgrades = document.querySelector("#defender-upgrades");
  const connectionError = document.querySelector("#connection-error");
  const linkVersionWarning = document.querySelector("#link-version-warning");
  const resultsContainer = document.querySelector("#results-container");
  const resultsImage = document.querySelector("#results-image");

  function showConnectionError() {
    connectionError.hidden = false;
  }

  function hideConnectionError() {
    connectionError.hidden = true;
  }

  function showLinkWarning(message) {
    linkVersionWarning.textContent = message;
    linkVersionWarning.hidden = false;
  }

  function hideLinkWarning() {
    linkVersionWarning.hidden = true;
  }

  function squadSizeKey(role, unitName) {
    return `sctmgtool.squad-size.${role}.${unitName}`;
  }

  function selectedUnitKey(role) {
    return `sctmgtool.selected-unit.${role}`;
  }

  function upgradeKey(role, unitName, upgradeSummary) {
    return `sctmgtool.upgrade.${role}.${unitName}.${upgradeSummary}`;
  }

  function getSavedSquadSize(role, unitName) {
    return localStorage.getItem(squadSizeKey(role, unitName));
  }

  function getSavedUnit(role) {
    return localStorage.getItem(selectedUnitKey(role));
  }

  function saveSquadSize(role, unitName, squadSize) {
    localStorage.setItem(squadSizeKey(role, unitName), squadSize);
  }

  function saveUnit(role, unitName) {
    localStorage.setItem(selectedUnitKey(role), unitName);
  }

  function getSavedUpgrade(role, unitName, upgradeSummary) {
    return localStorage.getItem(upgradeKey(role, unitName, upgradeSummary)) === "true";
  }

  function saveUpgrade(role, unitName, upgradeSummary, enabled) {
    localStorage.setItem(upgradeKey(role, unitName, upgradeSummary), enabled);
  }

  function getConfiguredSquadSize(unit, role) {
    const savedSquadSize = getSavedSquadSize(role, unit.name);
    const savedSquad = unit.squads.find((squad) => String(squad.models.max) === savedSquadSize);
    return savedSquad ? savedSquad.models.max : unit.squads[0].models.max;
  }

  function getFingerprint(unit, role) {
    const upgradeType = role === "attacker" ? "offensive" : "defensive";
    const configuration = unit.upgrades.reduce((value, upgrade) => {
      const isActive = upgrade.type.includes(upgradeType) && getSavedUpgrade(role, unit.name, upgrade.summary);
      return isActive ? value | (1 << upgrade.fingerprintIndex) : value;
    }, 0);

    return [unit.name, getConfiguredSquadSize(unit, role), configuration];
  }

  function encodeResultKey(attackerFingerprint, defenderFingerprint) {
    const payload = new TextEncoder().encode(JSON.stringify([attackerFingerprint, defenderFingerprint]));
    const binary = String.fromCharCode(...payload);
    return btoa(binary).replaceAll("+", "-").replaceAll("/", "_").replaceAll("=", "");
  }

  function decodeResultKey(resultKey) {
    if (!resultKey || resultKey.length > MAX_RESULT_KEY_LENGTH || !/^[A-Za-z0-9_-]+$/.test(resultKey)) {
      throw new Error("Invalid configuration encoding.");
    }

    const base64 = resultKey.replaceAll("-", "+").replaceAll("_", "/").padEnd(Math.ceil(resultKey.length / 4) * 4, "=");
    const binary = atob(base64);
    const payload = JSON.parse(new TextDecoder().decode(Uint8Array.from(binary, (character) => character.charCodeAt(0))));
    const isFingerprint = (fingerprint) =>
      Array.isArray(fingerprint) &&
      fingerprint.length === 3 &&
      typeof fingerprint[0] === "string" &&
      Number.isInteger(fingerprint[1]) &&
      Number.isInteger(fingerprint[2]) &&
      fingerprint[2] >= 0 &&
      fingerprint[2] <= 0x7fffffff;

    if (!Array.isArray(payload) || payload.length !== 2 || !payload.every(isFingerprint)) {
      throw new Error("Invalid configuration payload.");
    }

    return payload;
  }

  function makeUnitLabel(unitName) {
    return unitName
      .normalize("NFKD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/[^A-Za-z0-9]+/g, "-")
      .replace(/^-|-$/g, "");
  }

  function updateShareUrl(appVersion, resultKey, attackerFingerprint, defenderFingerprint) {
    const parameters = new URLSearchParams({
      app: appVersion,
      state: resultKey,
      label: `${makeUnitLabel(attackerFingerprint[0])}-vs-${makeUnitLabel(defenderFingerprint[0])}`,
    });
    const url = new URL(window.location.href);
    url.hash = parameters.toString();
    history.replaceState(null, "", url);
  }

  function readLinkedConfiguration() {
    if (window.location.hash.length > MAX_SHARE_FRAGMENT_LENGTH) {
      throw new Error("The configuration link is too long.");
    }

    const parameters = new URLSearchParams(window.location.hash.slice(1));
    const appVersion = parameters.get("app");
    const resultKey = parameters.get("state");

    if (appVersion === null && resultKey === null) {
      return null;
    }
    if (!appVersion || !resultKey) {
      throw new Error("The configuration link is incomplete.");
    }

    return { appVersion, fingerprints: decodeResultKey(resultKey) };
  }

  function validateLinkedFingerprint(fingerprint, role, unitsByName) {
    const [unitName, squadSize, configuration] = fingerprint;
    const unit = unitsByName.get(unitName);
    if (!unit || !unit.squads.some((squad) => squad.models.max === squadSize)) {
      throw new Error(`Unknown unit or squad size: ${unitName}.`);
    }

    const upgradeType = role === "attacker" ? "offensive" : "defensive";
    const allowedConfigurationMask = unit.upgrades.reduce(
      (mask, upgrade) => (upgrade.type.includes(upgradeType) ? mask | (1 << upgrade.fingerprintIndex) : mask),
      0,
    );
    if ((configuration & ~allowedConfigurationMask) !== 0) {
      throw new Error(`Invalid ${role} upgrade configuration.`);
    }
  }

  function applyLinkedFingerprint(fingerprint, role, unitsByName) {
    const [unitName, squadSize, configuration] = fingerprint;
    const unit = unitsByName.get(unitName);

    saveUnit(role, unitName);
    saveSquadSize(role, unitName, squadSize);
    const upgradeType = role === "attacker" ? "offensive" : "defensive";
    for (const upgrade of unit.upgrades) {
      if (upgrade.type.includes(upgradeType)) {
        saveUpgrade(role, unitName, upgrade.summary, Boolean(configuration & (1 << upgrade.fingerprintIndex)));
      }
    }
  }

  function updateSquadSizeRadios(unit, radioName, role) {
    const radios = document.querySelectorAll(`input[name="${radioName}"]`);
    const activeSquadSize = getConfiguredSquadSize(unit, role);
    const activeSquadIndex = unit.squads.findIndex((squad) => squad.models.max === activeSquadSize);

    radios.forEach((radio, index) => {
      const squad = unit.squads[index];
      const label = radio.closest("label");
      const value = label.querySelector("span");

      radio.checked = index === activeSquadIndex && Boolean(squad);
      radio.disabled = !squad;
      radio.value = squad ? squad.models.max : "0";
      value.textContent = squad ? squad.models.max : "-";
      label.classList.toggle("is-disabled", !squad);
    });
  }

  function updateWeapons(configuredWeapons, weapons) {
    const weaponRows = configuredWeapons.map((weapon) => {
      const row = document.createElement("li");

      row.textContent = weapon.text;
      row.classList.toggle("weapon--inactive", !weapon.active);
      return row;
    });

    if (weaponRows.length === 0) {
      const emptyRow = document.createElement("li");
      emptyRow.textContent = "-";
      weaponRows.push(emptyRow);
    }

    weapons.replaceChildren(...weaponRows);
  }

  function updateUpgrades(unit, upgrades, role, onChange) {
    const upgradeType = role === "attacker" ? "offensive" : "defensive";
    const relevantUpgrades = unit.upgrades.filter((upgrade) => upgrade.type.includes(upgradeType));
    const upgradeRows = relevantUpgrades.map((upgrade) => {
      const label = document.createElement("label");
      const checkbox = document.createElement("input");

      checkbox.type = "checkbox";
      checkbox.checked = getSavedUpgrade(role, unit.name, upgrade.summary);
      checkbox.addEventListener("change", () => {
        saveUpgrade(role, unit.name, upgrade.summary, checkbox.checked);
        onChange();
      });
      label.classList.add("upgrade");
      label.append(checkbox, document.createTextNode(` ${upgrade.summary}`));
      return label;
    });

    if (upgradeRows.length === 0) {
      const emptyRow = document.createElement("p");
      emptyRow.classList.add("placeholder");
      emptyRow.textContent = "-";
      upgradeRows.push(emptyRow);
    }

    upgrades.replaceChildren(...upgradeRows);
  }

  function updateUnitPanel(unit, upgrades, radioName, role, onUpgradeChange) {
    updateUpgrades(unit, upgrades, role, onUpgradeChange);
    updateSquadSizeRadios(unit, radioName, role);
  }

  try {
    const response = await fetch(apiUrl("/api/units"));

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const { cacheRevision, units } = await response.json();
    hideConnectionError();
    const factionOrder = { Terran: 0, Protoss: 1, Zerg: 2 };

    units.sort(
      (left, right) =>
        factionOrder[left.faction] - factionOrder[right.faction] || left.name.localeCompare(right.name),
    );

    for (const unit of units) {
      const option = new Option(unit.name, unit.name);
      attackerSelect.add(option.cloneNode(true));
      defenderSelect.add(option);
    }

    const unitsByName = new Map(units.map((unit) => [unit.name, unit]));
    let preserveLinkedUrl = false;
    try {
      const linkedConfiguration = readLinkedConfiguration();
      if (linkedConfiguration) {
        validateLinkedFingerprint(linkedConfiguration.fingerprints[0], "attacker", unitsByName);
        validateLinkedFingerprint(linkedConfiguration.fingerprints[1], "defender", unitsByName);
        applyLinkedFingerprint(linkedConfiguration.fingerprints[0], "attacker", unitsByName);
        applyLinkedFingerprint(linkedConfiguration.fingerprints[1], "defender", unitsByName);

        if (linkedConfiguration.appVersion !== cacheRevision.app) {
          preserveLinkedUrl = true;
          showLinkWarning(
            `This link was created with version ${linkedConfiguration.appVersion}. ` +
              `The current version is ${cacheRevision.app}, so the displayed configuration may differ.`,
          );
        }
      }
    } catch (error) {
      showLinkWarning("This configuration link is invalid and was ignored.");
      console.error("Could not load linked configuration:", error);
    }

    const unitNames = new Set(unitsByName.keys());
    attackerSelect.value = unitNames.has(getSavedUnit("attacker")) ? getSavedUnit("attacker") : "Marine";
    defenderSelect.value = unitNames.has(getSavedUnit("defender")) ? getSavedUnit("defender") : "Zealot";

    let configurationRequestController = null;
    let configurationResultKey = null;
    const updateConfiguredUnits = async (resultKey) => {
      if (configurationResultKey === resultKey) {
        return;
      }

      configurationRequestController?.abort();
      const controller = new AbortController();
      configurationRequestController = controller;
      configurationResultKey = resultKey;

      try {
        const response = await fetch(apiUrl(`/api/configurations/${cacheRevision.app}/${resultKey}`), { signal: controller.signal });
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const configuration = await response.json();
        if (configurationRequestController !== controller) {
          return;
        }

        attackerSummary.textContent = configuration.attacker.summary;
        defenderSummary.textContent = configuration.defender.summary;
        updateWeapons(configuration.attacker.weapons, attackerWeapons);
        hideConnectionError();
      } catch (error) {
        if (error.name === "AbortError") {
          return;
        }

        configurationResultKey = null;
        showConnectionError();
        console.error("Could not load configured units:", error);
      } finally {
        if (configurationRequestController === controller) {
          configurationRequestController = null;
        }
      }
    };

    const updateResults = () => {
      const attackerFingerprint = getFingerprint(unitsByName.get(attackerSelect.value), "attacker");
      const defenderFingerprint = getFingerprint(unitsByName.get(defenderSelect.value), "defender");
      const resultKey = encodeResultKey(attackerFingerprint, defenderFingerprint);
      if (!preserveLinkedUrl) {
        updateShareUrl(cacheRevision.app, resultKey, attackerFingerprint, defenderFingerprint);
      }

      void updateConfiguredUnits(resultKey);
      const resultUrl = apiUrl(`/api/results/${cacheRevision.app}/${cacheRevision.charts}/${resultKey}`);
      const expectedUrl = new URL(resultUrl, window.location.href).href;

      if (resultsImage.src === expectedUrl) {
        return;
      }

      resultsContainer.setAttribute("aria-busy", "true");
      const loadingTimer = window.setTimeout(() => {
        if (resultsImage.src === expectedUrl) {
          resultsContainer.classList.add("is-loading");
        }
      }, 30);
      const finishLoading = () => {
        window.clearTimeout(loadingTimer);
        if (resultsImage.src === expectedUrl) {
          resultsContainer.classList.remove("is-loading");
          resultsContainer.setAttribute("aria-busy", "false");
        }
      };
      resultsImage.onload = () => {
        finishLoading();
        hideConnectionError();
      };
      resultsImage.onerror = () => {
        finishLoading();
        showConnectionError();
      };
      resultsImage.src = resultUrl;
    };
    const updateResultsAfterUserChange = () => {
      preserveLinkedUrl = false;
      hideLinkWarning();
      updateResults();
    };
    const updateAttackerSquadSize = () =>
      {
        const unit = unitsByName.get(attackerSelect.value);
        updateUnitPanel(unit, attackerUpgrades, "attacker-size", "attacker", () => {
          updateAttackerSquadSize();
          updateResultsAfterUserChange();
        });
      };
    const updateDefenderSquadSize = () =>
      updateUnitPanel(
        unitsByName.get(defenderSelect.value),
        defenderUpgrades,
        "defender-size",
        "defender",
        () => {
          updateDefenderSquadSize();
          updateResultsAfterUserChange();
        },
      );

    attackerSelect.addEventListener("change", () => {
      saveUnit("attacker", attackerSelect.value);
      updateAttackerSquadSize();
      updateResultsAfterUserChange();
    });
    defenderSelect.addEventListener("change", () => {
      saveUnit("defender", defenderSelect.value);
      updateDefenderSquadSize();
      updateResultsAfterUserChange();
    });
    swapButton.addEventListener("click", () => {
      const attackerUnit = attackerSelect.value;
      attackerSelect.value = defenderSelect.value;
      defenderSelect.value = attackerUnit;
      attackerSelect.dispatchEvent(new Event("change"));
      defenderSelect.dispatchEvent(new Event("change"));
    });
    document.querySelectorAll('input[name="attacker-size"]').forEach((radio) => {
      radio.addEventListener("change", () => {
        if (radio.checked) {
          saveSquadSize("attacker", attackerSelect.value, radio.value);
          updateAttackerSquadSize();
          updateResultsAfterUserChange();
        }
      });
    });
    document.querySelectorAll('input[name="defender-size"]').forEach((radio) => {
      radio.addEventListener("change", () => {
        if (radio.checked) {
          saveSquadSize("defender", defenderSelect.value, radio.value);
          updateDefenderSquadSize();
          updateResultsAfterUserChange();
        }
      });
    });
    updateAttackerSquadSize();
    updateDefenderSquadSize();
    updateResults();
  } catch (error) {
    showConnectionError();
    console.error("Could not load units:", error);
  }
});
