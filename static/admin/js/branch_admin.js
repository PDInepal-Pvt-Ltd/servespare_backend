/**
 * Dynamic district dropdown based on province selection
 * This file handles the automatic update of district choices when province changes
 */

// Store the province-district mapping
const NEPAL_PROVINCE_DISTRICTS = {
  Koshi: [
    "Bhojpur",
    "Dhankuta",
    "Ilam",
    "Jhapa",
    "Khotang",
    "Morang",
    "Okhaldhunga",
    "Panchthar",
    "Sankhuwasabha",
    "Solukhumbu",
    "Sunsari",
    "Taplejung",
    "Terhathum",
    "Udayapur",
  ],
  Madhesh: [
    "Bara",
    "Dhanusha",
    "Mahottari",
    "Parsa",
    "Rautahat",
    "Saptari",
    "Sarlahi",
    "Siraha",
  ],
  Bagmati: [
    "Bhaktapur",
    "Chitwan",
    "Dhading",
    "Dolakha",
    "Kathmandu",
    "Kavrepalanchok",
    "Lalitpur",
    "Makwanpur",
    "Nuwakot",
    "Ramechhap",
    "Rasuwa",
    "Sindhuli",
    "Sindhupalchok",
  ],
  Gandaki: [
    "Baglung",
    "Gorkha",
    "Kaski",
    "Lamjung",
    "Manang",
    "Mustang",
    "Myagdi",
    "Nawalpur",
    "Parbat",
    "Syangja",
    "Tanahun",
  ],
  Lumbini: [
    "Arghakhanchi",
    "Banke",
    "Bardiya",
    "Dang",
    "Gulmi",
    "Kapilvastu",
    "Palpa",
    "Pyuthan",
    "Rolpa",
    "Rupandehi",
    "Rukum East",
    "Nawalparasi West",
  ],
  Karnali: [
    "Dailekh",
    "Dolpa",
    "Humla",
    "Jajarkot",
    "Jumla",
    "Kalikot",
    "Mugu",
    "Rukum West",
    "Salyan",
    "Surkhet",
  ],
  Sudurpashchim: [
    "Achham",
    "Baitadi",
    "Bajhang",
    "Bajura",
    "Dadeldhura",
    "Darchula",
    "Doti",
    "Kailali",
    "Kanchanpur",
  ],
};

/**
 * Update district dropdown based on selected province
 * @param {string} provinceValue - The selected province value
 */
function updateDistrictDropdown(provinceValue) {
  const districtSelect = document.getElementById("id_district");

  if (!districtSelect) {
    return;
  }

  // Clear existing options except the first placeholder
  districtSelect.innerHTML =
    '<option value="">--- Select District ---</option>';

  // If a province is selected, add its districts
  if (provinceValue && NEPAL_PROVINCE_DISTRICTS[provinceValue]) {
    const districts = NEPAL_PROVINCE_DISTRICTS[provinceValue];
    districts.forEach(function (district) {
      const option = document.createElement("option");
      option.value = district;
      option.textContent = district;
      districtSelect.appendChild(option);
    });
  }

  // Reset district selection
  districtSelect.value = "";
}

// Initialize on page load
document.addEventListener("DOMContentLoaded", function () {
  const provinceSelect = document.getElementById("id_province");

  if (provinceSelect) {
    // Update district dropdown on province change
    provinceSelect.addEventListener("change", function () {
      updateDistrictDropdown(this.value);
    });

    // Initial update if province is already selected
    if (provinceSelect.value) {
      updateDistrictDropdown(provinceSelect.value);
    }
  }
});
