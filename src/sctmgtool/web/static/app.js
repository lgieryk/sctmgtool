// SPDX-License-Identifier: MIT
// Copyright (c) 2026 Łukasz Gieryk

document.addEventListener("DOMContentLoaded", async () => {
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
  const resultsContainer = document.querySelector("#results-container");
  const resultsImage = document.querySelector("#results-image");

  function showConnectionError() {
    connectionError.hidden = false;
  }

  function hideConnectionError() {
    connectionError.hidden = true;
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

  function getAttackerWeaponBatches(unit, squadSize) {
    const activatingWeaponNames = new Set(
      unit.upgrades.filter((upgrade) => upgrade.activatesWeapon).map((upgrade) => upgrade.activatesWeapon),
    );
    const batches = [];
    const defaultWeaponTypes = new Set();

    for (const weapon of unit.weapons) {
      if (activatingWeaponNames.has(weapon.name)) {
        continue;
      }

      const weaponType = ["E", "C"].includes(weapon.range) ? weapon.range : "R";
      const isSidearm = weapon.tags.includes("Sidearm");
      if (isSidearm || !defaultWeaponTypes.has(weaponType)) {
        batches.push({ name: weapon.name, modelNum: squadSize });
        defaultWeaponTypes.add(weaponType);
      }
    }

    for (const upgrade of unit.upgrades) {
      if (!upgrade.activatesWeapon || !upgrade.type.includes("offensive") || !getSavedUpgrade("attacker", unit.name, upgrade.summary)) {
        continue;
      }

      const weapon = unit.weapons.find((candidate) => candidate.name === upgrade.activatesWeapon);
      if (weapon.exchangeFor) {
        const batchIndex = batches.findIndex((batch) => batch.name === weapon.exchangeFor);
        if (batchIndex === -1) {
          continue;
        }

        const batch = batches[batchIndex];
        const modelNum = weapon.tags.includes("Specialist") ? 1 : batch.modelNum;
        if (batch.modelNum > modelNum) {
          batch.modelNum -= modelNum;
        } else {
          batches.splice(batchIndex, 1);
        }
        batches.push({ name: weapon.name, modelNum });
      } else if (weapon.tags.includes("Sidearm")) {
        batches.push({ name: weapon.name, modelNum: weapon.tags.includes("Specialist") ? 1 : squadSize });
      }
    }

    return batches;
  }

  function updateWeapons(unit, weapons, squadSize) {
    const batches = getAttackerWeaponBatches(unit, squadSize);
    const weaponRows = unit.weapons.map((weapon) => {
      const row = document.createElement("li");
      const batch = batches.find((candidate) => candidate.name === weapon.name);

      row.textContent = `${String(batch?.modelNum ?? 0).padStart(2)}x ${weapon.summary}`;
      row.classList.toggle("weapon--inactive", !batch);
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

  function updateUnitPanel(unit, summary, upgrades, radioName, role, onUpgradeChange) {
    summary.textContent = unit.summary;
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

    const unitNames = new Set(units.map((unit) => unit.name));
    attackerSelect.value = unitNames.has(getSavedUnit("attacker")) ? getSavedUnit("attacker") : "Marine";
    defenderSelect.value = unitNames.has(getSavedUnit("defender")) ? getSavedUnit("defender") : "Zealot";

    const unitsByName = new Map(units.map((unit) => [unit.name, unit]));
    const updateResults = () => {
      const resultKey = encodeResultKey(
        getFingerprint(unitsByName.get(attackerSelect.value), "attacker"),
        getFingerprint(unitsByName.get(defenderSelect.value), "defender"),
      );
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
    const updateAttackerSquadSize = () =>
      {
        const unit = unitsByName.get(attackerSelect.value);
        updateWeapons(unit, attackerWeapons, getConfiguredSquadSize(unit, "attacker"));
        updateUnitPanel(unit, attackerSummary, attackerUpgrades, "attacker-size", "attacker", () => {
          updateAttackerSquadSize();
          updateResults();
        });
      };
    const updateDefenderSquadSize = () =>
      updateUnitPanel(
        unitsByName.get(defenderSelect.value),
        defenderSummary,
        defenderUpgrades,
        "defender-size",
        "defender",
        () => {
          updateDefenderSquadSize();
          updateResults();
        },
      );

    attackerSelect.addEventListener("change", () => {
      saveUnit("attacker", attackerSelect.value);
      updateAttackerSquadSize();
      updateResults();
    });
    defenderSelect.addEventListener("change", () => {
      saveUnit("defender", defenderSelect.value);
      updateDefenderSquadSize();
      updateResults();
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
          updateResults();
        }
      });
    });
    document.querySelectorAll('input[name="defender-size"]').forEach((radio) => {
      radio.addEventListener("change", () => {
        if (radio.checked) {
          saveSquadSize("defender", defenderSelect.value, radio.value);
          updateDefenderSquadSize();
          updateResults();
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
