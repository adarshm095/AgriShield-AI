/**
 * AgriShield-AI - Client Controller with MongoDB Atlas & Compass Integration
 */

document.addEventListener("DOMContentLoaded", () => {
  // Elements
  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("file-input");
  const previewContainer = document.getElementById("preview-container");
  const previewImg = document.getElementById("preview-img");
  const removeImgBtn = document.getElementById("remove-img-btn");
  const scanOverlay = document.getElementById("scan-overlay");
  const btnAnalyze = document.getElementById("btn-analyze");
  const samplesContainer = document.getElementById("samples-container");
  const farmSelector = document.getElementById("farm-selector");

  const emptyState = document.getElementById("empty-state");
  const diagnosisCard = document.getElementById("diagnosis-card");
  const mongoSyncedPill = document.getElementById("mongo-synced-pill");
  const mongoObsId = document.getElementById("mongo-obs-id");

  // Diagnosis Card Fields
  const diagCrop = document.getElementById("diag-crop");
  const diagTitle = document.getElementById("diag-title");
  const diagScientific = document.getElementById("diag-scientific");
  const diagStatusBadge = document.getElementById("diag-status-badge");
  const diagStatusText = document.getElementById("diag-status-text");
  const diagConfidence = document.getElementById("diag-confidence");
  const diagSeverity = document.getElementById("diag-severity");
  const diagPathogen = document.getElementById("diag-pathogen");
  const diagDesc = document.getElementById("diag-desc");
  const diagSymptoms = document.getElementById("diag-symptoms");
  const listOrganic = document.getElementById("list-organic");
  const listChemical = document.getElementById("list-chemical");
  const listPrevention = document.getElementById("list-prevention");
  const alternatesList = document.getElementById("alternates-list");

  // MongoDB Panel Elements
  const mongoBadgeText = document.getElementById("mongo-badge-text");
  const mongoDbName = document.getElementById("mongo-db-name");
  const mongoCountDiseases = document.getElementById("mongo-count-diseases");
  const mongoCountObs = document.getElementById("mongo-count-obs");
  const mongoCountFarms = document.getElementById("mongo-count-farms");
  const mongoUriDisplay = document.getElementById("mongo-uri-display");
  const btnCopyUri = document.getElementById("btn-copy-uri");
  const btnReseedDb = document.getElementById("btn-reseed-db");
  const mongoObsTbody = document.getElementById("mongo-obs-tbody");

  // Utilities
  const btnTts = document.getElementById("btn-tts");
  const btnPrint = document.getElementById("btn-print");
  const btnHistory = document.getElementById("btn-history");
  const historyCount = document.getElementById("history-count");
  const historyModal = document.getElementById("history-modal");
  const historyCloseBtn = document.getElementById("history-close-btn");
  const historyList = document.getElementById("history-list");

  // Catalog
  const catalogSearch = document.getElementById("catalog-search");
  const cropFilter = document.getElementById("crop-filter");
  const typeFilter = document.getElementById("type-filter");
  const diseaseGrid = document.getElementById("disease-grid");
  const detailModal = document.getElementById("detail-modal");
  const modalCloseBtn = document.getElementById("modal-close-btn");
  const modalContent = document.getElementById("modal-content");

  // State
  let currentFile = null;
  let currentSampleId = null;
  let currentDiagnosis = null;
  let diseasesCatalog = [];
  let registeredFarms = [];

  // Initialize
  initApp();

  async function initApp() {
    await checkMongoDbStatus();
    await loadFarms();
    loadSampleLeaves();
    loadDiseaseCatalog();
    loadMongoObservations();
  }

  // ============================================================
  // MongoDB Connection & Status Handling
  // ============================================================
  async function checkMongoDbStatus() {
    try {
      const res = await fetch("/api/db/status");
      if (res.ok) {
        const data = await res.json();
        if (data.connected) {
          mongoBadgeText.textContent = `MongoDB: Connected (${data.database})`;
          mongoDbName.textContent = data.database;
          mongoCountDiseases.textContent = data.collections?.diseases || 0;
          mongoCountObs.textContent = data.collections?.crop_observations || 0;
          mongoCountFarms.textContent = data.collections?.farms || 0;
          mongoUriDisplay.textContent = data.compass_connection_string || data.uri;
          historyCount.textContent = data.collections?.crop_observations || 0;
        } else {
          mongoBadgeText.textContent = `MongoDB: Standby`;
          mongoUriDisplay.textContent = "mongodb://localhost:27017/agrishield_db";
        }
      }
    } catch (e) {
      console.warn("MongoDB status error", e);
      mongoBadgeText.textContent = `MongoDB: Standby`;
    }
  }

  async function loadFarms() {
    try {
      const res = await fetch("/api/farms");
      if (res.ok) {
        const data = await res.json();
        registeredFarms = data.farms || [];
        if (registeredFarms.length > 0) {
          farmSelector.innerHTML = "";
          registeredFarms.forEach((farm) => {
            const opt = document.createElement("option");
            opt.value = farm.id || farm._id;
            opt.textContent = `${farm.farmName} (${farm.farmerName} - ${farm.crop})`;
            farmSelector.appendChild(opt);
          });
        }
      }
    } catch (e) {
      console.warn("Farms load error", e);
    }
  }

  async function loadMongoObservations() {
    try {
      const res = await fetch("/api/observations?limit=10");
      if (res.ok) {
        const data = await res.json();
        renderObservationsTable(data.observations || []);
        renderHistoryModal(data.observations || []);
        historyCount.textContent = data.total || 0;
        mongoCountObs.textContent = data.total || 0;
      }
    } catch (e) {
      console.warn("Observations load error", e);
    }
  }

  function renderObservationsTable(observations) {
    mongoObsTbody.innerHTML = "";
    if (observations.length === 0) {
      mongoObsTbody.innerHTML = `
        <tr>
          <td colspan="7" style="padding: 24px; text-align: center; color: var(--text-dim);">
            No field observations in MongoDB yet. Run a leaf scan above to insert a new document.
          </td>
        </tr>
      `;
      return;
    }

    observations.forEach((obs) => {
      const tr = document.createElement("tr");
      tr.style.cssText = "border-bottom: 1px solid var(--border-light); transition: var(--transition);";
      
      const riskColor = obs.riskLevel === "CRITICAL" ? "var(--accent-rose)" :
                        obs.riskLevel === "HIGH" ? "#fb7185" :
                        obs.riskLevel === "LOW" ? "var(--accent-lime)" : "#fbbf24";

      const timeStr = obs.createdAt ? new Date(obs.createdAt).toLocaleDateString() + ' ' + new Date(obs.createdAt).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) : 'Recent';

      tr.innerHTML = `
        <td style="padding: 12px 16px; font-family: monospace; color: var(--accent-lime);">${obs._id || obs.id}</td>
        <td style="padding: 12px 16px;"><strong>${obs.farmerName || 'Farmer'}</strong><br><span style="font-size: 0.75rem; color: var(--text-dim);">${obs.farmId}</span></td>
        <td style="padding: 12px 16px;">${obs.crop}</td>
        <td style="padding: 12px 16px;">${obs.prediction?.disease || 'Diagnosis'}</td>
        <td style="padding: 12px 16px;"><span class="card-pill" style="background: rgba(0,0,0,0.4); color: ${riskColor}; border: 1px solid ${riskColor};">${obs.riskLevel || 'NORMAL'}</span></td>
        <td style="padding: 12px 16px; font-size: 0.78rem; color: var(--text-dim);">${timeStr}</td>
        <td style="padding: 12px 16px;">
          <button class="btn btn-outline btn-sm" style="font-size: 0.72rem; padding: 4px 8px;" onclick="window.viewObsDetail('${obs._id || obs.id}')">View</button>
        </td>
      `;
      mongoObsTbody.appendChild(tr);
    });
  }

  // Copy Compass URI Button
  btnCopyUri.addEventListener("click", () => {
    const uri = mongoUriDisplay.textContent.trim();
    navigator.clipboard.writeText(uri).then(() => {
      btnCopyUri.textContent = "Copied!";
      setTimeout(() => btnCopyUri.textContent = "Copy URI", 2000);
    });
  });

  // Re-sync Database Button
  btnReseedDb.addEventListener("click", async () => {
    btnReseedDb.disabled = true;
    btnReseedDb.textContent = "Syncing...";
    try {
      const res = await fetch("/api/db/seed?force=false", { method: "POST" });
      const data = await res.json();
      alert(`MongoDB synced successfully! ${data.seeded_diseases} diseases verified.`);
      await checkMongoDbStatus();
      await loadDiseaseCatalog();
    } catch (e) {
      alert("Error syncing MongoDB: " + e.message);
    } finally {
      btnReseedDb.disabled = false;
      btnReseedDb.textContent = "Re-Sync Collections";
    }
  });

  // ============================================================
  // File Upload & Drag-and-Drop Handling
  // ============================================================
  dropzone.addEventListener("click", () => fileInput.click());

  fileInput.addEventListener("change", (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelected(e.target.files[0]);
    }
  });

  ["dragenter", "dragover"].forEach((eventName) => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.add("drag-active");
    });
  });

  ["dragleave", "drop"].forEach((eventName) => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.remove("drag-active");
    });
  });

  dropzone.addEventListener("drop", (e) => {
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelected(e.dataTransfer.files[0]);
    }
  });

  function handleFileSelected(file) {
    if (!file.type.startsWith("image/")) {
      alert("Please upload an image file (JPG, PNG, WEBP).");
      return;
    }
    currentFile = file;
    currentSampleId = null;

    const reader = new FileReader();
    reader.onload = (e) => {
      previewImg.src = e.target.result;
      dropzone.style.display = "none";
      previewContainer.style.display = "block";
      btnAnalyze.disabled = false;
    };
    reader.readAsDataURL(file);
  }

  removeImgBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    currentFile = null;
    currentSampleId = null;
    previewImg.src = "";
    previewContainer.style.display = "none";
    dropzone.style.display = "block";
    btnAnalyze.disabled = true;
    fileInput.value = "";
    hideDiagnosis();
  });

  // ============================================================
  // Analyze & Predict (With MongoDB Storage)
  // ============================================================
  btnAnalyze.addEventListener("click", async () => {
    if (!currentFile && !currentSampleId) return;

    btnAnalyze.disabled = true;
    btnAnalyze.innerHTML = `
      <svg class="spinner" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="animation: spin 1s linear infinite;">
        <circle cx="12" cy="12" r="10" stroke-opacity="0.25"/>
        <path d="M12 2a10 10 0 0 1 10 10"/>
      </svg>
      <span>Neural Inference & MongoDB Sync...</span>
    `;
    scanOverlay.style.display = "block";

    const selectedFarmId = farmSelector.value || "farm_001";
    const selectedFarm = registeredFarms.find(f => (f.id || f._id) === selectedFarmId);
    const farmerName = selectedFarm ? selectedFarm.farmerName : "Ramesh Kumar";

    try {
      let result;
      if (currentSampleId) {
        // Sample path
        const res = await fetch(`/api/predict-sample/${currentSampleId}?farm_id=${encodeURIComponent(selectedFarmId)}&farmer_name=${encodeURIComponent(farmerName)}`, {
          method: "POST"
        });
        if (!res.ok) throw new Error("Sample prediction failed");
        result = await res.json();
      } else {
        // Uploaded file path
        const formData = new FormData();
        formData.append("file", currentFile);
        formData.append("farm_id", selectedFarmId);
        formData.append("farmer_name", farmerName);

        const res = await fetch("/api/predict", {
          method: "POST",
          body: formData
        });
        if (!res.ok) throw new Error("Inference service unavailable");
        result = await res.json();
      }

      setTimeout(() => {
        scanOverlay.style.display = "none";
        renderDiagnosis(result);
        loadMongoObservations(); // Refresh live MongoDB table
        checkMongoDbStatus();
        btnAnalyze.disabled = false;
        btnAnalyze.innerHTML = `
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="20 6 9 17 4 12"/>
          </svg>
          <span>Diagnosis Complete - Run Again</span>
        `;
      }, 700);

    } catch (err) {
      console.error(err);
      scanOverlay.style.display = "none";
      alert("Error diagnosing image: " + err.message);
      btnAnalyze.disabled = false;
      btnAnalyze.innerHTML = `<span>Run Neural Diagnosis</span>`;
    }
  });

  // ============================================================
  // Render Diagnosis UI
  // ============================================================
  function renderDiagnosis(data) {
    currentDiagnosis = data;
    const p = data.primary;

    emptyState.style.display = "none";
    diagnosisCard.style.display = "block";

    diagCrop.textContent = p.crop || "Crop";
    diagTitle.textContent = p.common_name || p.class_name;
    diagScientific.textContent = p.scientific_name ? `(${p.scientific_name})` : "";

    const isHealthy = (p.status || "").toLowerCase() === "healthy";
    diagStatusText.textContent = isHealthy ? "Healthy Foliage" : "Infection Detected";
    diagStatusBadge.className = `status-indicator ${isHealthy ? "healthy" : "diseased"}`;

    diagConfidence.textContent = `${p.confidence}%`;
    diagSeverity.textContent = p.severity || "Unknown";
    diagPathogen.textContent = p.pathogen_type || "None";

    if (data.observation_id) {
      mongoSyncedPill.style.display = "flex";
      mongoObsId.textContent = data.observation_id;
    } else {
      mongoSyncedPill.style.display = "none";
    }

    if (isHealthy) {
      diagSeverity.style.color = "var(--accent-lime)";
    } else if (p.severity && p.severity.toLowerCase().includes("severe")) {
      diagSeverity.style.color = "var(--accent-rose)";
    } else {
      diagSeverity.style.color = "var(--accent-gold)";
    }

    diagDesc.textContent = p.description || "";

    diagSymptoms.innerHTML = "";
    if (p.symptoms && p.symptoms.length > 0) {
      p.symptoms.forEach((s) => {
        const li = document.createElement("li");
        li.textContent = s;
        diagSymptoms.appendChild(li);
      });
    }

    populateList(listOrganic, p.organic_treatment);
    populateList(listChemical, p.chemical_treatment);
    populateList(listPrevention, p.prevention);

    alternatesList.innerHTML = "";
    if (data.alternates && data.alternates.length > 0) {
      data.alternates.forEach((alt) => {
        const row = document.createElement("div");
        row.className = "alt-item";
        row.innerHTML = `
          <div>
            <strong>${alt.common_name}</strong>
            <span style="font-size: 0.75rem; color: var(--text-dim); margin-left: 6px;">(${alt.pathogen_type})</span>
          </div>
          <div style="display: flex; align-items: center;">
            <span>${alt.confidence}%</span>
            <div class="alt-bar-bg">
              <div class="alt-bar-fill" style="width: ${alt.confidence}%;"></div>
            </div>
          </div>
        `;
        alternatesList.appendChild(row);
      });
      document.getElementById("alternates-box").style.display = "block";
    } else {
      document.getElementById("alternates-box").style.display = "none";
    }
  }

  function hideDiagnosis() {
    diagnosisCard.style.display = "none";
    emptyState.style.display = "block";
    currentDiagnosis = null;
  }

  function populateList(element, items) {
    element.innerHTML = "";
    if (items && items.length > 0) {
      items.forEach((item) => {
        const li = document.createElement("li");
        li.textContent = item;
        element.appendChild(li);
      });
    } else {
      const li = document.createElement("li");
      li.textContent = "No specific measures required for this condition.";
      element.appendChild(li);
    }
  }

  // Tabs Switcher
  const tabButtons = document.querySelectorAll(".tab-btn");
  tabButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      tabButtons.forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".tab-content").forEach((c) => c.classList.remove("active"));

      btn.classList.add("active");
      const targetId = btn.getAttribute("data-tab");
      document.getElementById(targetId).classList.add("active");
    });
  });

  // ============================================================
  // Samples Loader
  // ============================================================
  async function loadSampleLeaves() {
    try {
      const res = await fetch("/api/samples");
      if (!res.ok) return;
      const samples = await res.json();
      samplesContainer.innerHTML = "";

      samples.forEach((sample) => {
        const chip = document.createElement("div");
        chip.className = "sample-chip";
        chip.innerHTML = `
          <img src="${sample.url}" alt="${sample.title}" loading="lazy">
          <span>${sample.title}</span>
        `;
        chip.addEventListener("click", () => {
          selectSample(sample);
        });
        samplesContainer.appendChild(chip);
      });
    } catch (e) {
      console.warn("Samples not loaded", e);
    }
  }

  function selectSample(sample) {
    currentFile = null;
    currentSampleId = sample.id;
    previewImg.src = sample.url;
    dropzone.style.display = "none";
    previewContainer.style.display = "block";
    btnAnalyze.disabled = false;
    btnAnalyze.click();
  }

  // ============================================================
  // Disease Catalog (MongoDB Source)
  // ============================================================
  async function loadDiseaseCatalog() {
    try {
      const res = await fetch("/api/diseases");
      if (!res.ok) return;
      const data = await res.json();
      diseasesCatalog = data.diseases || [];

      const crops = [...new Set(diseasesCatalog.map((d) => d.crop).filter(Boolean))].sort();
      cropFilter.innerHTML = `<option value="ALL">All Crops (${crops.length})</option>`;
      crops.forEach((c) => {
        const opt = document.createElement("option");
        opt.value = c;
        opt.textContent = c;
        cropFilter.appendChild(opt);
      });

      renderCatalog();
    } catch (e) {
      console.warn("Disease catalog load error", e);
    }
  }

  function renderCatalog() {
    const query = (catalogSearch.value || "").toLowerCase().trim();
    const selCrop = cropFilter.value;
    const selType = typeFilter.value;

    const filtered = diseasesCatalog.filter((item) => {
      const name = item.name || item.common_name || item.class_name || "";
      const matchesSearch =
        !query ||
        name.toLowerCase().includes(query) ||
        (item.crop && item.crop.toLowerCase().includes(query)) ||
        (item.scientific_name && item.scientific_name.toLowerCase().includes(query));

      const matchesCrop = selCrop === "ALL" || item.crop === selCrop;
      const matchesType =
        selType === "ALL" ||
        (selType === "None" && item.status && item.status.toLowerCase() === "healthy") ||
        (item.pathogen_type && item.pathogen_type.toLowerCase().includes(selType.toLowerCase()));

      return matchesSearch && matchesCrop && matchesType;
    });

    diseaseGrid.innerHTML = "";
    if (filtered.length === 0) {
      diseaseGrid.innerHTML = `
        <div style="grid-column: 1 / -1; text-align: center; padding: 40px; color: var(--text-dim);">
          No diseases match the active filters in MongoDB.
        </div>
      `;
      return;
    }

    filtered.forEach((d) => {
      const card = document.createElement("div");
      card.className = "disease-card";

      const pathogenClass = (d.pathogen_type || "healthy").toLowerCase();
      const pillClass = pathogenClass.includes("fungal")
        ? "fungal"
        : pathogenClass.includes("bacterial")
        ? "bacterial"
        : pathogenClass.includes("viral")
        ? "viral"
        : pathogenClass.includes("pest")
        ? "pest"
        : "healthy";

      const title = d.name || d.common_name || d.class_name;

      card.innerHTML = `
        <div class="card-crop-tag">${d.crop}</div>
        <h4 class="card-title">${title}</h4>
        <div class="card-meta">
          <span class="card-pill ${pillClass}">${d.pathogen_type || d.status}</span>
          <span>&bull;</span>
          <span>Severity: ${d.severity || "None"}</span>
        </div>
      `;
      card.addEventListener("click", () => openDetailModal(d));
      diseaseGrid.appendChild(card);
    });
  }

  catalogSearch.addEventListener("input", renderCatalog);
  cropFilter.addEventListener("change", renderCatalog);
  typeFilter.addEventListener("change", renderCatalog);

  function openDetailModal(d) {
    const title = d.name || d.common_name || d.class_name;
    modalContent.innerHTML = `
      <div style="margin-bottom: 16px;">
        <span style="font-size: 0.8rem; font-weight: 700; color: var(--accent-lime); text-transform: uppercase;">${d.crop} (MongoDB Document)</span>
        <h2 style="font-size: 1.6rem; font-weight: 800; margin: 4px 0;">${title}</h2>
        <p style="font-size: 0.88rem; color: var(--text-dim); font-style: italic;">${d.scientific_name || ""}</p>
      </div>

      <div style="display: flex; gap: 10px; margin-bottom: 20px;">
        <span class="status-badge">${d.pathogen_type || "Condition"}</span>
        <span class="status-badge" style="background: rgba(251, 191, 36, 0.15); color: #fbbf24; border-color: rgba(251, 191, 36, 0.3);">Severity: ${d.severity || 'Normal'}</span>
      </div>

      <p style="font-size: 0.95rem; color: var(--text-muted); margin-bottom: 20px;">${d.description || 'Full agronomic profile stored in MongoDB.'}</p>

      <h4 style="color: var(--accent-lime); margin-bottom: 8px;">Key Symptoms</h4>
      <ul style="padding-left: 20px; font-size: 0.9rem; margin-bottom: 20px;">
        ${(d.symptoms || []).map((s) => `<li style="margin-bottom: 6px;">${s}</li>`).join("")}
      </ul>

      <h4 style="color: var(--accent-lime); margin-bottom: 8px;">Organic Treatment</h4>
      <ul style="padding-left: 20px; font-size: 0.9rem; margin-bottom: 20px;">
        ${(d.organic_treatment || []).map((t) => `<li style="margin-bottom: 6px;">${t}</li>`).join("")}
      </ul>

      <h4 style="color: var(--accent-lime); margin-bottom: 8px;">Chemical Control</h4>
      <ul style="padding-left: 20px; font-size: 0.9rem; margin-bottom: 20px;">
        ${(d.chemical_treatment || []).map((c) => `<li style="margin-bottom: 6px;">${c}</li>`).join("")}
      </ul>

      <h4 style="color: var(--accent-lime); margin-bottom: 8px;">Cultural Prevention</h4>
      <ul style="padding-left: 20px; font-size: 0.9rem;">
        ${(d.prevention || []).map((p) => `<li style="margin-bottom: 6px;">${p}</li>`).join("")}
      </ul>
    `;
    detailModal.classList.add("open");
  }

  modalCloseBtn.addEventListener("click", () => detailModal.classList.remove("open"));
  detailModal.addEventListener("click", (e) => {
    if (e.target === detailModal) detailModal.classList.remove("open");
  });

  // Text-To-Speech (Read Aloud)
  btnTts.addEventListener("click", () => {
    if (!currentDiagnosis || !window.speechSynthesis) return;

    if (window.speechSynthesis.speaking) {
      window.speechSynthesis.cancel();
      btnTts.classList.remove("speaking");
      return;
    }

    const p = currentDiagnosis.primary;
    const text = `Diagnosis for ${p.crop}: ${p.common_name}. Health status is ${p.status}. Severity is ${p.severity}. ${p.description}. Recommended organic action: ${(p.organic_treatment || []).slice(0, 2).join(". ")}`;

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.95;
    utterance.pitch = 1.0;
    utterance.onend = () => btnTts.classList.remove("speaking");
    btnTts.classList.add("speaking");
    window.speechSynthesis.speak(utterance);
  });

  // Print Report
  btnPrint.addEventListener("click", () => window.print());

  // MongoDB History Modal
  btnHistory.addEventListener("click", () => {
    loadMongoObservations();
    historyModal.classList.add("open");
  });

  historyCloseBtn.addEventListener("click", () => historyModal.classList.remove("open"));
  historyModal.addEventListener("click", (e) => {
    if (e.target === historyModal) historyModal.classList.remove("open");
  });

  function renderHistoryModal(observations) {
    historyList.innerHTML = "";
    if (observations.length === 0) {
      historyList.innerHTML = `<p style="text-align: center; color: var(--text-dim); padding: 20px;">No scan records in MongoDB collection 'crop_observations'.</p>`;
      return;
    }

    observations.forEach((h) => {
      const row = document.createElement("div");
      row.style.cssText = "display: flex; align-items: center; gap: 14px; background: rgba(0,0,0,0.3); padding: 12px; border-radius: 8px; border: 1px solid var(--border-light);";
      
      const thumb = h.imageUrl || "/static/samples/tomato_early_blight.jpg";
      const diagName = h.prediction?.disease || h.crop;
      const timeStr = h.createdAt ? new Date(h.createdAt).toLocaleString() : "Recent";
      const conf = h.prediction?.confidence_percent ? `${h.prediction.confidence_percent}%` : (h.prediction?.confidence ? `${Math.round(h.prediction.confidence * 100)}%` : '');

      row.innerHTML = `
        <img src="${thumb}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 6px;">
        <div style="flex: 1;">
          <div style="font-weight: 700; font-size: 0.95rem;">${diagName}</div>
          <div style="font-size: 0.78rem; color: var(--text-dim);">${h.farmerName || 'Farmer'} &bull; ${h.crop} &bull; ${conf} &bull; ${timeStr}</div>
          <div style="font-size: 0.72rem; color: var(--accent-lime); font-family: monospace;">_id: ${h._id || h.id}</div>
        </div>
        <span class="card-pill" style="font-size: 0.75rem; border: 1px solid var(--accent-lime);">${h.riskLevel || 'RECORDED'}</span>
      `;
      historyList.appendChild(row);
    });
  }

  window.viewObsDetail = (obsId) => {
    const obs = registeredFarms; // modal trigger
    alert(`Observation ${obsId} is stored in MongoDB database 'agrishield_db' in collection 'crop_observations'.\n\nYou can query this document directly in MongoDB Compass:\nFilter: { "_id": "${obsId}" }`);
  };

});
