/**
 * AgriShield-AI - Client Controller
 * Farmer-Centric Crop Health Diagnostics & Field Advisory
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

  // Diagnosis Card Fields
  const emptyState = document.getElementById("empty-state");
  const diagnosisCard = document.getElementById("diagnosis-card");
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
  const diagFieldTag = document.getElementById("diag-field-tag");

  // AI Agronomist Copilot Elements
  const aiQueryForm = document.getElementById("ai-query-form");
  const aiUserQuery = document.getElementById("ai-user-query");
  const aiAnswerCard = document.getElementById("ai-answer-card");

  // Tables & Lists
  const obsTbody = document.getElementById("obs-tbody");
  const historyList = document.getElementById("history-list");
  const historyCount = document.getElementById("history-count");
  const historyTotalTag = document.getElementById("history-total-tag");

  // Catalog
  const catalogSearch = document.getElementById("catalog-search");
  const cropFilter = document.getElementById("crop-filter");
  const typeFilter = document.getElementById("type-filter");
  const diseaseGrid = document.getElementById("disease-grid");

  // Modals
  const authModal = document.getElementById("auth-modal");
  const btnOpenAuth = document.getElementById("btn-open-auth");
  const authModalCloseBtn = document.getElementById("auth-modal-close-btn");
  const tabLoginBtn = document.getElementById("tab-login-btn");
  const tabRegisterBtn = document.getElementById("tab-register-btn");
  const formLogin = document.getElementById("form-login");
  const formRegister = document.getElementById("form-register");
  const loginErrorMsg = document.getElementById("login-error-msg");
  const regErrorMsg = document.getElementById("reg-error-msg");
  const userProfilePill = document.getElementById("user-profile-pill");
  const userAvatarInitial = document.getElementById("user-avatar-initial");
  const userDisplayName = document.getElementById("user-display-name");
  const btnLogout = document.getElementById("btn-logout");

  const farmModal = document.getElementById("farm-modal");
  const btnAddFarmTrigger = document.getElementById("btn-add-farm-trigger");
  const btnAddFarmMain = document.getElementById("btn-add-farm-main");
  const farmModalCloseBtn = document.getElementById("farm-modal-close-btn");
  const formAddFarm = document.getElementById("form-add-farm");

  const historyModal = document.getElementById("history-modal");
  const btnHistory = document.getElementById("btn-history");
  const historyCloseBtn = document.getElementById("history-close-btn");
  const btnViewAllScans = document.getElementById("btn-view-all-scans");

  const detailModal = document.getElementById("detail-modal");
  const modalCloseBtn = document.getElementById("modal-close-btn");
  const modalContent = document.getElementById("modal-content");

  // Utilities
  const btnTts = document.getElementById("btn-tts");
  const btnPrint = document.getElementById("btn-print");
  const btnLang = document.getElementById("btn-lang");
  const langLabel = document.getElementById("lang-label");

  // State
  let currentFile = null;
  let currentSampleId = null;
  let currentDiagnosis = null;
  let diseasesCatalog = [];
  let registeredFarms = [];
  let currentUser = null;
  let currentLanguage = localStorage.getItem("agrishield_lang") || "en";

  // Bilingual Dictionary
  const translations = {
    en: {
      lang_label: "हिन्दी",
      brand_tag: "Smart Crop Doctor",
      nav_doctor: "Crop Doctor",
      nav_fields: "My Fields",
      nav_catalog: "Disease Library",
      nav_advisory: "Spraying Advisory",
      nav_scans: "Field Scans",
      auth_btn: "Farmer Login",
      hero_pill: "🌱 AI-Powered Plant Health & Harvest Protection",
      hero_title: 'Protect Your Harvest with <span class="gradient-text">Instant Crop Disease Diagnosis</span>',
      hero_sub: "Upload or snap a photo of any crop leaf. Get accurate disease diagnosis, verified organic and spray remedies, and tailored advice from our AI Agronomist to save your yield.",
      scan_title: "Plant Leaf Health Scanner",
      scan_desc: "Select your field, upload a leaf photo, or click a quick sample to diagnose health issues.",
      select_field: "🌾 Select Field / Crop:",
      dropzone_main: "Take a photo or browse leaf image",
      dropzone_sub: "Supports JPG, PNG, WEBP. Close-up photos on infected leaves give best results.",
      btn_diagnose: "Diagnose Plant Health",
      empty_title: "Awaiting Leaf Photo",
      empty_desc: "Select your field and upload a leaf image to receive an immediate diagnosis, organic treatments, and spraying guidelines.",
      tab_organic: "🌿 Organic Remedies",
      tab_chemical: "🧪 Spray Guide (Dawa)",
      tab_prevention: "🛡️ Prevention & Care",
      ai_title: "Ask AI Crop Doctor About This Disease",
      ai_placeholder: "Ask specific questions (e.g. spray schedule, dosage)..."
    },
    hi: {
      lang_label: "English",
      brand_tag: "स्मार्ट फसल डॉक्टर",
      nav_doctor: "फसल डॉक्टर",
      nav_fields: "मेरे खेत",
      nav_catalog: "रोग पुस्तकालय",
      nav_advisory: "छिड़काव सलाह",
      nav_scans: "खेत जांच",
      auth_btn: "किसान लॉगिन",
      hero_pill: "🌱 आधुनिक फसल सुरक्षा एवं पौध रोग परामर्श",
      hero_title: '<span class="gradient-text">फसल रोग की तुरंत पहचान</span> और सही उपचार',
      hero_sub: "पत्ती का फोटो खींचें या अपलोड करें। रोग की सटीक पहचान, असरदार जैविक व देसी उपाय, और छिड़काव की सही मात्रा तुरंत पाएं।",
      scan_title: "पत्ती रोग जांच केंद्र",
      scan_desc: "अपना खेत चुनें और पत्ती की फोटो अपलोड करके तुरंत जांच करें।",
      select_field: "🌾 अपना खेत / फसल चुनें:",
      dropzone_main: "पत्ती की फोटो खींचें या गैलरी से चुनें",
      dropzone_sub: "JPG, PNG, WEBP स्वीकार्य हैं। रोगग्रस्त पत्ती की साफ फोटो लें।",
      btn_diagnose: "फसल स्वास्थ्य की जांच करें",
      empty_title: "पत्ती की फोटो का इंतजार है",
      empty_desc: "अपना खेत चुनें और पत्ती की तस्वीर अपलोड करें ताकि तुरंत रोग पहचान और सटीक उपचार मिल सके।",
      tab_organic: "🌿 जैविक व देसी उपाय",
      tab_chemical: "🧪 दवा छिड़काव गाइड",
      tab_prevention: "🛡️ बचाव व सावधानियां",
      ai_title: "फसल डॉक्टर से इस बीमारी के बारे में पूछें",
      ai_placeholder: "अपने सवाल पूछें (जैसे: दवा की मात्रा, नीम तेल का प्रयोग)..."
    }
  };

  // Initialize
  initApp();

  async function initApp() {
    applyLanguage(currentLanguage);
    setupEventListeners();
    await checkAuthSession();
    await loadFarms();
    loadSampleLeaves();
    loadDiseaseCatalog();
    loadObservations();
  }

  // ============================================================
  // Language Toggle
  // ============================================================
  function applyLanguage(lang) {
    currentLanguage = lang;
    localStorage.setItem("agrishield_lang", lang);
    const t = translations[lang] || translations.en;

    langLabel.textContent = t.lang_label;
    const brandTag = document.getElementById("brand-tag");
    if (brandTag) brandTag.textContent = t.brand_tag;

    const navScanner = document.getElementById("nav-scanner");
    if (navScanner) navScanner.textContent = t.nav_doctor;

    const navFields = document.getElementById("nav-fields");
    if (navFields) navFields.textContent = t.nav_fields;

    const navCatalog = document.getElementById("nav-catalog");
    if (navCatalog) navCatalog.textContent = t.nav_catalog;

    const navAdvisory = document.getElementById("nav-advisory");
    if (navAdvisory) navAdvisory.textContent = t.nav_advisory;

    const authBtnText = document.getElementById("auth-btn-text");
    if (authBtnText) authBtnText.textContent = t.auth_btn;

    const heroPillText = document.getElementById("hero-pill-text");
    if (heroPillText) heroPillText.innerHTML = `<span>${t.hero_pill}</span>`;

    const heroTitle = document.getElementById("hero-title");
    if (heroTitle) heroTitle.innerHTML = t.hero_title;

    const heroSub = document.getElementById("hero-subtitle");
    if (heroSub) heroSub.textContent = t.hero_sub;

    const panelScanTitle = document.querySelector("#panel-scan-title span");
    if (panelScanTitle) panelScanTitle.textContent = t.scan_title;

    const panelScanDesc = document.getElementById("panel-scan-desc");
    if (panelScanDesc) panelScanDesc.textContent = t.scan_desc;

    const labelSelectField = document.getElementById("label-select-field");
    if (labelSelectField) labelSelectField.textContent = t.select_field;

    const dropzoneMainText = document.getElementById("dropzone-main-text");
    if (dropzoneMainText) dropzoneMainText.textContent = t.dropzone_main;

    const dropzoneSubText = document.getElementById("dropzone-sub-text");
    if (dropzoneSubText) dropzoneSubText.textContent = t.dropzone_sub;

    const btnAnalyzeText = document.getElementById("btn-analyze-text");
    if (btnAnalyzeText) btnAnalyzeText.textContent = t.btn_diagnose;

    const emptyStateTitle = document.getElementById("empty-state-title");
    if (emptyStateTitle) emptyStateTitle.textContent = t.empty_title;

    const emptyStateDesc = document.getElementById("empty-state-desc");
    if (emptyStateDesc) emptyStateDesc.textContent = t.empty_desc;

    const tabOrganicBtn = document.getElementById("tab-organic-btn");
    if (tabOrganicBtn) tabOrganicBtn.textContent = t.tab_organic;

    const tabChemicalBtn = document.getElementById("tab-chemical-btn");
    if (tabChemicalBtn) tabChemicalBtn.textContent = t.tab_chemical;

    const tabPreventionBtn = document.getElementById("tab-prevention-btn");
    if (tabPreventionBtn) tabPreventionBtn.textContent = t.tab_prevention;

    const aiAdvisorTitle = document.getElementById("ai-advisor-title");
    if (aiAdvisorTitle) aiAdvisorTitle.textContent = t.ai_title;

    if (aiUserQuery) aiUserQuery.placeholder = t.ai_placeholder;
  }

  // ============================================================
  // Authentication & Session Management
  // ============================================================
  async function checkAuthSession() {
    const token = localStorage.getItem("agrishield_token");
    if (!token) {
      renderLoggedOutState();
      return;
    }

    try {
      const res = await fetch("/api/auth/me", {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        currentUser = data.user;
        renderLoggedInState(currentUser);
      } else {
        localStorage.removeItem("agrishield_token");
        renderLoggedOutState();
      }
    } catch (e) {
      renderLoggedOutState();
    }
  }

  function renderLoggedInState(user) {
    btnOpenAuth.style.display = "none";
    userProfilePill.style.display = "flex";
    userDisplayName.textContent = user.name || "Farmer";
    userAvatarInitial.textContent = (user.name || "F").charAt(0).toUpperCase();
  }

  function renderLoggedOutState() {
    currentUser = null;
    btnOpenAuth.style.display = "inline-flex";
    userProfilePill.style.display = "none";
  }

  // Auth Modal Tab Switcher
  tabLoginBtn.addEventListener("click", () => {
    tabLoginBtn.classList.add("active");
    tabRegisterBtn.classList.remove("active");
    formLogin.style.display = "block";
    formRegister.style.display = "none";
    loginErrorMsg.style.display = "none";
  });

  tabRegisterBtn.addEventListener("click", () => {
    tabRegisterBtn.classList.add("active");
    tabLoginBtn.classList.remove("active");
    formRegister.style.display = "block";
    formLogin.style.display = "none";
    regErrorMsg.style.display = "none";
  });

  btnOpenAuth.addEventListener("click", () => {
    authModal.classList.add("active");
  });

  authModalCloseBtn.addEventListener("click", () => {
    authModal.classList.remove("active");
  });

  btnLogout.addEventListener("click", () => {
    localStorage.removeItem("agrishield_token");
    renderLoggedOutState();
    loadFarms();
    loadObservations();
  });

  // Login Form Submission
  formLogin.addEventListener("submit", async (e) => {
    e.preventDefault();
    loginErrorMsg.style.display = "none";
    const identifier = document.getElementById("login-identifier").value;
    const password = document.getElementById("login-password").value;

    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ identifier, password })
      });
      const data = await res.json();
      if (res.ok && data.status === "success") {
        localStorage.setItem("agrishield_token", data.token);
        currentUser = data.user;
        renderLoggedInState(currentUser);
        authModal.classList.remove("active");
        formLogin.reset();
        await loadFarms();
        await loadObservations();
      } else {
        loginErrorMsg.textContent = data.detail || "Login failed. Please check credentials.";
        loginErrorMsg.style.display = "block";
      }
    } catch (err) {
      loginErrorMsg.textContent = "Server error during login. Please try again.";
      loginErrorMsg.style.display = "block";
    }
  });

  // Registration Form Submission
  formRegister.addEventListener("submit", async (e) => {
    e.preventDefault();
    regErrorMsg.style.display = "none";
    const name = document.getElementById("reg-name").value;
    const email = document.getElementById("reg-email").value;
    const phone = document.getElementById("reg-phone").value;
    const location = document.getElementById("reg-location").value;
    const password = document.getElementById("reg-password").value;

    try {
      const res = await fetch("/api/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email, phone, location, password })
      });
      const data = await res.json();
      if (res.ok && data.status === "success") {
        localStorage.setItem("agrishield_token", data.token);
        currentUser = data.user;
        renderLoggedInState(currentUser);
        authModal.classList.remove("active");
        formRegister.reset();
        await loadFarms();
        await loadObservations();
      } else {
        regErrorMsg.textContent = data.detail || "Registration failed.";
        regErrorMsg.style.display = "block";
      }
    } catch (err) {
      regErrorMsg.textContent = "Server error during registration. Please try again.";
      regErrorMsg.style.display = "block";
    }
  });

  // ============================================================
  // Dynamic Field & Farm Management
  // ============================================================
  async function loadFarms() {
    try {
      const url = currentUser ? `/api/farms?farmer_id=${currentUser.id}` : "/api/farms";
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        registeredFarms = data.farms || [];
        populateFarmDropdown(registeredFarms);
      }
    } catch (e) {
      console.warn("Farms load error", e);
    }
  }

  function populateFarmDropdown(farms) {
    farmSelector.innerHTML = "";
    if (farms.length === 0) {
      const opt = document.createElement("option");
      opt.value = "farm_default";
      opt.textContent = "General Field - Unassigned";
      farmSelector.appendChild(opt);
      return;
    }

    farms.forEach((farm) => {
      const opt = document.createElement("option");
      opt.value = farm.id || farm._id;
      const farmerTag = farm.farmerName ? `(${farm.farmerName})` : "";
      opt.textContent = `${farm.farmName} - ${farm.crop} ${farmerTag}`;
      farmSelector.appendChild(opt);
    });

    const fieldCountLabel = document.getElementById("label-field-count");
    if (fieldCountLabel) {
      fieldCountLabel.textContent = `${farms.length} fields available`;
    }
  }

  // Open Add Farm Modal
  const openFarmModal = () => farmModal.classList.add("active");
  if (btnAddFarmTrigger) btnAddFarmTrigger.addEventListener("click", openFarmModal);
  if (btnAddFarmMain) btnAddFarmMain.addEventListener("click", openFarmModal);
  if (farmModalCloseBtn) farmModalCloseBtn.addEventListener("click", () => farmModal.classList.remove("active"));

  // Add Farm Submission
  formAddFarm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const farmName = document.getElementById("farm-input-name").value;
    const crop = document.getElementById("farm-input-crop").value;
    const area = parseFloat(document.getElementById("farm-input-area").value) || 1.0;
    const sowingDate = document.getElementById("farm-input-date").value;
    const location = document.getElementById("farm-input-location").value;

    const payload = {
      farmName,
      crop,
      area,
      sowingDate,
      location,
      farmerId: currentUser ? currentUser.id : "usr_guest",
      farmerName: currentUser ? currentUser.name : "Farmer"
    };

    try {
      const res = await fetch("/api/farms", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        const data = await res.json();
        farmModal.classList.remove("active");
        formAddFarm.reset();
        await loadFarms();
        // Select newly created farm
        if (data.farm && (data.farm.id || data.farm._id)) {
          farmSelector.value = data.farm.id || data.farm._id;
        }
      }
    } catch (err) {
      alert("Could not register field. Please try again.");
    }
  });

  // ============================================================
  // Image Upload & Leaf Scanner
  // ============================================================
  function setupEventListeners() {
    btnLang.addEventListener("click", () => {
      const nextLang = currentLanguage === "en" ? "hi" : "en";
      applyLanguage(nextLang);
    });

    dropzone.addEventListener("click", () => fileInput.click());

    dropzone.addEventListener("dragover", (e) => {
      e.preventDefault();
      dropzone.classList.add("dragover");
    });

    dropzone.addEventListener("dragleave", () => {
      dropzone.classList.remove("dragover");
    });

    dropzone.addEventListener("drop", (e) => {
      e.preventDefault();
      dropzone.classList.remove("dragover");
      if (e.dataTransfer.files && e.dataTransfer.files[0]) {
        handleFileSelect(e.dataTransfer.files[0]);
      }
    });

    fileInput.addEventListener("change", (e) => {
      if (e.target.files && e.target.files[0]) {
        handleFileSelect(e.target.files[0]);
      }
    });

    removeImgBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      resetInput();
    });

    btnAnalyze.addEventListener("click", () => {
      runDiagnosis();
    });

    // Tab buttons in diagnosis card
    const tabs = document.querySelectorAll(".tabs-header .tab-btn");
    tabs.forEach((tab) => {
      tab.addEventListener("click", () => {
        const target = tab.getAttribute("data-tab");
        if (!target) return;
        document.querySelectorAll(".tab-btn").forEach((t) => t.classList.remove("active"));
        document.querySelectorAll(".tab-content").forEach((c) => c.classList.remove("active"));
        tab.classList.add("active");
        const activeContent = document.getElementById(target);
        if (activeContent) activeContent.classList.add("active");
      });
    });

    // History Modal Triggers
    btnHistory.addEventListener("click", () => historyModal.classList.add("active"));
    historyCloseBtn.addEventListener("click", () => historyModal.classList.remove("active"));
    if (btnViewAllScans) {
      btnViewAllScans.addEventListener("click", () => historyModal.classList.add("active"));
    }

    // Catalog Search & Filters
    catalogSearch.addEventListener("input", filterCatalog);
    cropFilter.addEventListener("change", filterCatalog);
    typeFilter.addEventListener("change", filterCatalog);

    modalCloseBtn.addEventListener("click", () => detailModal.classList.remove("active"));

    // TTS & Print
    btnTts.addEventListener("click", speakDiagnosis);
    btnPrint.addEventListener("click", () => window.print());

    // AI Agronomist Query Form
    aiQueryForm.addEventListener("submit", (e) => {
      e.preventDefault();
      const q = aiUserQuery.value.trim();
      if (q) askAiAdvisor(q);
    });

    // AI Chip buttons
    document.querySelectorAll(".ai-chip").forEach((chip) => {
      chip.addEventListener("click", () => {
        const q = chip.getAttribute("data-q");
        if (q) {
          aiUserQuery.value = q;
          askAiAdvisor(q);
        }
      });
    });
  }

  function handleFileSelect(file) {
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
      previewContainer.style.display = "flex";
      btnAnalyze.disabled = false;
    };
    reader.readAsDataURL(file);
  }

  function resetInput() {
    currentFile = null;
    currentSampleId = null;
    fileInput.value = "";
    previewImg.src = "";
    dropzone.style.display = "block";
    previewContainer.style.display = "none";
    btnAnalyze.disabled = true;
  }

  // Preloaded Samples Strip
  async function loadSampleLeaves() {
    try {
      const res = await fetch("/api/samples");
      if (res.ok) {
        const samples = await res.json();
        renderSampleChips(samples);
      }
    } catch (e) {
      console.warn("Samples load error", e);
    }
  }

  function renderSampleChips(samples) {
    samplesContainer.innerHTML = "";
    samples.forEach((sample) => {
      const chip = document.createElement("div");
      chip.className = "sample-chip";
      const cropName = sample.crop || (sample.class_name ? sample.class_name.split("___")[0].replace(/_/g, " ") : sample.title.split(" ")[0]);
      chip.innerHTML = `
        <img src="${sample.url}" alt="${sample.title}">
        <div class="sample-chip-text">
          <div class="sample-chip-crop">${cropName}</div>
          <div class="sample-chip-name">${sample.title.replace(/Leaf|Disease/gi, "").trim()}</div>
        </div>
      `;
      chip.addEventListener("click", () => {
        currentSampleId = sample.id;
        currentFile = null;
        previewImg.src = sample.url;
        dropzone.style.display = "none";
        previewContainer.style.display = "flex";
        btnAnalyze.disabled = false;
        runDiagnosis();
      });
      samplesContainer.appendChild(chip);
    });
  }

  // ============================================================
  // Running Diagnosis
  // ============================================================
  async function runDiagnosis() {
    scanOverlay.style.display = "flex";
    btnAnalyze.disabled = true;

    const selectedFarmId = farmSelector.value || "farm_001";
    const selectedFarm = registeredFarms.find((f) => (f.id || f._id) === selectedFarmId);
    const farmerName = currentUser ? currentUser.name : (selectedFarm ? selectedFarm.farmerName : "Farmer");
    const farmerId = currentUser ? currentUser.id : "usr_guest";

    try {
      let res;
      if (currentSampleId) {
        res = await fetch(`/api/predict-sample/${currentSampleId}?farm_id=${selectedFarmId}&farmer_name=${encodeURIComponent(farmerName)}&farmer_id=${farmerId}`, {
          method: "POST"
        });
      } else if (currentFile) {
        const formData = new FormData();
        formData.append("file", currentFile);
        formData.append("farm_id", selectedFarmId);
        formData.append("farmer_name", farmerName);
        formData.append("farmer_id", farmerId);
        res = await fetch("/api/predict", {
          method: "POST",
          body: formData
        });
      }

      if (res && res.ok) {
        const data = await res.json();
        currentDiagnosis = data;
        renderDiagnosis(data, selectedFarm);
        await loadObservations();
      } else {
        alert("Diagnosis analysis failed. Please try another image.");
      }
    } catch (err) {
      console.error(err);
      alert("Error contacting diagnostic server.");
    } finally {
      scanOverlay.style.display = "none";
      btnAnalyze.disabled = false;
    }
  }

  function renderDiagnosis(data, selectedFarm) {
    const primary = data.primary;
    if (!primary) return;

    emptyState.style.display = "none";
    diagnosisCard.style.display = "block";

    diagCrop.textContent = primary.crop || "Crop";
    diagTitle.textContent = primary.common_name || primary.class_name;
    diagScientific.textContent = primary.scientific_name || "";

    const isHealthy = (primary.status || "").toLowerCase() === "healthy";
    if (isHealthy) {
      diagStatusBadge.className = "status-indicator healthy";
      diagStatusText.textContent = currentLanguage === "hi" ? "✓ फसल स्वस्थ है" : "✓ Crop Healthy";
    } else {
      diagStatusBadge.className = "status-indicator diseased";
      diagStatusText.textContent = currentLanguage === "hi" ? "उपचार आवश्यक" : "Needs Attention";
    }

    diagConfidence.textContent = `${primary.confidence}%`;
    diagSeverity.textContent = primary.severity || "Moderate";
    diagPathogen.textContent = primary.pathogen_type || "Fungal";

    const farmName = selectedFarm ? selectedFarm.farmName : "Field 1";
    diagFieldTag.textContent = farmName;

    diagDesc.textContent = primary.description || "";

    // Symptoms
    diagSymptoms.innerHTML = "";
    (primary.symptoms || []).forEach((sym) => {
      const li = document.createElement("li");
      li.textContent = sym;
      diagSymptoms.appendChild(li);
    });

    // Organic remedies
    listOrganic.innerHTML = "";
    (primary.organic_treatment || []).forEach((rem) => {
      const li = document.createElement("li");
      li.textContent = rem;
      listOrganic.appendChild(li);
    });

    // Chemical sprays
    listChemical.innerHTML = "";
    (primary.chemical_treatment || []).forEach((chem) => {
      const li = document.createElement("li");
      li.textContent = chem;
      listChemical.appendChild(li);
    });

    // Prevention
    listPrevention.innerHTML = "";
    (primary.prevention || []).forEach((prev) => {
      const li = document.createElement("li");
      li.textContent = prev;
      listPrevention.appendChild(li);
    });

    // Alternates
    alternatesList.innerHTML = "";
    (data.alternates || []).forEach((alt) => {
      const row = document.createElement("div");
      row.style.cssText = "display: flex; justify-content: space-between; font-size: 0.85rem; padding: 4px 8px; background: rgba(255,255,255,0.03); border-radius: 6px;";
      row.innerHTML = `<span>${alt.common_name}</span><strong style="color: var(--emerald-400);">${alt.confidence}%</strong>`;
      alternatesList.appendChild(row);
    });

    // Reset AI advisor card
    aiAnswerCard.style.display = "none";
    aiAnswerCard.textContent = "";
  }

  // ============================================================
  // Interactive AI Agronomist Copilot
  // ============================================================
  async function askAiAdvisor(question) {
    if (!currentDiagnosis || !currentDiagnosis.primary) {
      alert("Please perform a leaf diagnosis first so the doctor has your crop context.");
      return;
    }

    aiAnswerCard.style.display = "block";
    aiAnswerCard.textContent = currentLanguage === "hi" ? "डॉक्टर परामर्श तैयार हो रहा है..." : "Consulting Agri-Doctor...";

    try {
      const res = await fetch("/api/ai/advisor", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: question,
          crop: currentDiagnosis.primary.crop,
          disease: currentDiagnosis.primary.common_name,
          severity: currentDiagnosis.primary.severity,
          language: currentLanguage
        })
      });

      if (res.ok) {
        const data = await res.json();
        aiAnswerCard.textContent = data.answer;
      } else {
        aiAnswerCard.textContent = "Could not retrieve doctor advice at this moment.";
      }
    } catch (e) {
      aiAnswerCard.textContent = "Consultation error. Please try again.";
    }
  }

  // ============================================================
  // Observations & Recent Field Reports
  // ============================================================
  async function loadObservations() {
    try {
      const url = currentUser ? `/api/observations?farmer_id=${currentUser.id}` : "/api/observations";
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        const obs = data.observations || [];
        renderObservationsTable(obs);
        renderHistoryModal(obs);
        historyCount.textContent = obs.length;
        if (historyTotalTag) historyTotalTag.textContent = `${obs.length} saved scans`;
      }
    } catch (e) {
      console.warn("Observations load error", e);
    }
  }

  function renderObservationsTable(observations) {
    obsTbody.innerHTML = "";
    if (observations.length === 0) {
      obsTbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-muted); padding: 24px;">No crop observations yet. Diagnose your first leaf above!</td></tr>`;
      return;
    }

    observations.slice(0, 8).forEach((item) => {
      const tr = document.createElement("tr");
      const riskClass = (item.riskLevel || "").toLowerCase() === "low" ? "healthy" : "diseased";
      const dateStr = item.createdAt ? new Date(item.createdAt).toLocaleDateString() : "Today";
      const diagName = item.prediction ? item.prediction.disease : "Healthy";

      tr.innerHTML = `
        <td><strong>${item.farmerName || "Farmer"}</strong> <span style="font-size: 0.75rem; color: var(--emerald-400);">(${item.farmId || "Field"})</span></td>
        <td>${item.crop || "Unknown"}</td>
        <td>${diagName}</td>
        <td><span class="status-indicator ${riskClass}" style="padding: 2px 8px; font-size: 0.75rem;">${item.riskLevel || "MODERATE"}</span></td>
        <td>${dateStr}</td>
        <td>
          <button class="btn btn-outline btn-sm delete-obs-btn" data-id="${item.id || item._id}" style="padding: 4px 8px; font-size: 0.75rem; color: var(--status-danger);">Delete</button>
        </td>
      `;
      obsTbody.appendChild(tr);
    });

    // Delete buttons
    document.querySelectorAll(".delete-obs-btn").forEach((btn) => {
      btn.addEventListener("click", async (e) => {
        const obsId = e.target.getAttribute("data-id");
        if (confirm("Delete this scan record?")) {
          await deleteObservation(obsId);
        }
      });
    });
  }

  function renderHistoryModal(observations) {
    historyList.innerHTML = "";
    if (observations.length === 0) {
      historyList.innerHTML = `<p style="text-align: center; color: var(--text-muted); padding: 20px;">No scan history found.</p>`;
      return;
    }

    observations.forEach((item) => {
      const div = document.createElement("div");
      div.style.cssText = "background: var(--bg-surface); border: 1px solid var(--border-light); border-radius: 10px; padding: 14px; display: flex; align-items: center; justify-content: space-between;";
      const diagName = item.prediction ? item.prediction.disease : "Diagnosis";
      const dateStr = item.createdAt ? new Date(item.createdAt).toLocaleString() : "";

      div.innerHTML = `
        <div>
          <div style="font-size: 0.75rem; color: var(--emerald-400); font-weight: 700;">${item.crop} - ${item.farmerName}</div>
          <div style="font-size: 1rem; font-weight: 800; color: var(--text-title);">${diagName}</div>
          <div style="font-size: 0.78rem; color: var(--text-muted);">${dateStr}</div>
        </div>
        <div style="display: flex; gap: 8px;">
          <button class="btn btn-outline btn-sm delete-history-btn" data-id="${item.id || item._id}" style="color: var(--status-danger);">Delete</button>
        </div>
      `;
      historyList.appendChild(div);
    });

    document.querySelectorAll(".delete-history-btn").forEach((btn) => {
      btn.addEventListener("click", async (e) => {
        const obsId = e.target.getAttribute("data-id");
        if (confirm("Delete this observation?")) {
          await deleteObservation(obsId);
        }
      });
    });
  }

  async function deleteObservation(obsId) {
    try {
      const res = await fetch(`/api/observations/${obsId}`, { method: "DELETE" });
      if (res.ok) {
        await loadObservations();
      }
    } catch (e) {
      console.warn("Delete observation error", e);
    }
  }

  // ============================================================
  // Disease Library & Catalog
  // ============================================================
  async function loadDiseaseCatalog() {
    try {
      const res = await fetch("/api/diseases");
      if (res.ok) {
        const data = await res.json();
        diseasesCatalog = data.diseases || [];
        populateCropFilter(diseasesCatalog);
        renderDiseaseCards(diseasesCatalog);
      }
    } catch (e) {
      console.warn("Disease catalog load error", e);
    }
  }

  function populateCropFilter(diseases) {
    const crops = Array.from(new Set(diseases.map((d) => d.crop))).sort();
    cropFilter.innerHTML = `<option value="ALL">All Crops (${crops.length})</option>`;
    crops.forEach((c) => {
      const opt = document.createElement("option");
      opt.value = c;
      opt.textContent = c;
      cropFilter.appendChild(opt);
    });
  }

  function renderDiseaseCards(diseases) {
    diseaseGrid.innerHTML = "";
    diseases.forEach((dis) => {
      const card = document.createElement("div");
      card.className = "disease-card";
      const isHealthy = (dis.status || "").toLowerCase() === "healthy";
      const statusBadge = isHealthy ? "✓ Healthy" : (dis.pathogen_type || "Fungal");

      card.innerHTML = `
        <div style="display: flex; align-items: center; justify-content: space-between;">
          <span class="disease-card-crop">${dis.crop}</span>
          <span style="font-size: 0.72rem; color: ${isHealthy ? 'var(--emerald-400)' : 'var(--status-warning)'}; font-weight: 700;">${statusBadge}</span>
        </div>
        <div class="disease-card-title">${dis.common_name || dis.name}</div>
        <div class="disease-card-desc">${dis.description || "View symptoms and treatment options..."}</div>
      `;
      card.addEventListener("click", () => openDiseaseModal(dis));
      diseaseGrid.appendChild(card);
    });
  }

  function filterCatalog() {
    const query = catalogSearch.value.toLowerCase().trim();
    const selCrop = cropFilter.value;
    const selType = typeFilter.value;

    const filtered = diseasesCatalog.filter((dis) => {
      const nameMatch = (dis.common_name || dis.name || "").toLowerCase().includes(query) ||
                        (dis.crop || "").toLowerCase().includes(query) ||
                        (dis.pathogen_type || "").toLowerCase().includes(query);
      const cropMatch = selCrop === "ALL" || dis.crop.toLowerCase() === selCrop.toLowerCase();
      const typeMatch = selType === "ALL" ||
                        (selType === "None" ? (dis.status || "").toLowerCase() === "healthy" : (dis.pathogen_type || "").toLowerCase() === selType.toLowerCase());

      return nameMatch && cropMatch && typeMatch;
    });

    renderDiseaseCards(filtered);
  }

  function openDiseaseModal(dis) {
    modalContent.innerHTML = `
      <div style="font-size: 0.8rem; font-weight: 800; color: var(--emerald-400); text-transform: uppercase;">${dis.crop}</div>
      <h2 style="font-size: 1.4rem; color: var(--text-title); margin: 4px 0 12px;">${dis.common_name || dis.name}</h2>
      <p style="font-size: 0.9rem; color: var(--text-muted); margin-bottom: 16px;">${dis.description || ""}</p>
      
      <div style="font-size: 0.88rem; font-weight: 700; color: var(--emerald-400); margin-bottom: 6px;">🌿 Organic Remedies:</div>
      <ul style="padding-left: 20px; font-size: 0.85rem; margin-bottom: 14px;">
        ${(dis.organic_treatment || []).map((t) => `<li>${t}</li>`).join("")}
      </ul>

      <div style="font-size: 0.88rem; font-weight: 700; color: var(--status-warning); margin-bottom: 6px;">🧪 Chemical Controls:</div>
      <ul style="padding-left: 20px; font-size: 0.85rem; margin-bottom: 14px;">
        ${(dis.chemical_treatment || []).map((t) => `<li>${t}</li>`).join("")}
      </ul>

      <div style="font-size: 0.88rem; font-weight: 700; color: var(--status-info); margin-bottom: 6px;">🛡️ Prevention:</div>
      <ul style="padding-left: 20px; font-size: 0.85rem;">
        ${(dis.prevention || []).map((t) => `<li>${t}</li>`).join("")}
      </ul>
    `;
    detailModal.classList.add("active");
  }

  // ============================================================
  // Utilities: Speech Synthesis
  // ============================================================
  function speakDiagnosis() {
    if (!("speechSynthesis" in window) || !currentDiagnosis || !currentDiagnosis.primary) {
      alert("Text-to-speech is not supported or no diagnosis is active.");
      return;
    }

    const p = currentDiagnosis.primary;
    const text = `Crop ${p.crop}. Diagnosis: ${p.common_name}. Severity: ${p.severity}. Recommended organic action: ${(p.organic_treatment && p.organic_treatment[0]) || 'Keep leaves dry'}.`;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.95;
    window.speechSynthesis.speak(utterance);
  }

});
