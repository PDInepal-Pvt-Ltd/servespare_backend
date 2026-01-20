/**
 * Django Admin - SalesOrder Province-District Cascading Dropdowns
 * 
 * This script handles the cascading behavior where selecting a province
 * populates the district dropdown with only the districts in that province.
 */

(function() {
    'use strict';

    const PROVINCE_DISTRICTS = {
        'Koshi': ['Bhojpur', 'Dhankuta', 'Ilam', 'Jhapa', 'Khotang', 'Morang', 'Okhaldhunga', 'Panchthar', 'Sankhuwasabha', 'Solukhumbu', 'Sunsari', 'Taplejung', 'Terhathum', 'Udayapur'],
        'Madhesh': ['Bara', 'Dhanusha', 'Mahottari', 'Parsa', 'Rautahat', 'Saptari', 'Sarlahi', 'Siraha'],
        'Bagmati': ['Bhaktapur', 'Chitwan', 'Dhading', 'Dolakha', 'Kathmandu', 'Kavrepalanchok', 'Lalitpur', 'Makwanpur', 'Nuwakot', 'Ramechhap', 'Rasuwa', 'Sindhuli', 'Sindhupalchok'],
        'Gandaki': ['Baglung', 'Gorkha', 'Kaski', 'Lamjung', 'Manang', 'Mustang', 'Myagdi', 'Nawalpur', 'Parbat', 'Syangja', 'Tanahun'],
        'Lumbini': ['Arghakhanchi', 'Banke', 'Bardiya', 'Dang', 'Gulmi', 'Kapilvastu', 'Palpa', 'Pyuthan', 'Rolpa', 'Rupandehi', 'Rukum East', 'Nawalparasi West'],
        'Karnali': ['Dailekh', 'Dolpa', 'Humla', 'Jajarkot', 'Jumla', 'Kalikot', 'Mugu', 'Rukum West', 'Salyan', 'Surkhet'],
        'Sudurpashchim': ['Achham', 'Baitadi', 'Bajhang', 'Bajura', 'Dadeldhura', 'Darchula', 'Doti', 'Kailali', 'Kanchanpur'],
    };

    function initializeCascadingDropdown() {
        const provinceSelect = document.getElementById('id_delivery_province');
        const districtSelect = document.getElementById('id_delivery_district');

        if (!provinceSelect || !districtSelect) {
            return;
        }

        /**
         * Update district dropdown based on selected province
         */
        function updateDistricts() {
            const selectedProvince = provinceSelect.value;
            const currentDistrict = districtSelect.value;

            // Clear current options
            districtSelect.innerHTML = '<option value="">--- Select District ---</option>';

            if (selectedProvince && PROVINCE_DISTRICTS[selectedProvince]) {
                const districts = PROVINCE_DISTRICTS[selectedProvince];

                districts.forEach(district => {
                    const option = document.createElement('option');
                    option.value = district;
                    option.textContent = district;

                    // Re-select if it was previously selected
                    if (district === currentDistrict) {
                        option.selected = true;
                    }

                    districtSelect.appendChild(option);
                });
            }

            // Re-enable district select if province is selected
            districtSelect.disabled = !selectedProvince;
        }

        // Add change listener to province dropdown
        provinceSelect.addEventListener('change', updateDistricts);

        // Initialize on page load if a province is already selected
        updateDistricts();
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeCascadingDropdown);
    } else {
        initializeCascadingDropdown();
    }

    // Also handle dynamic forms (in case admin uses inline editing)
    // Observer for dynamically added forms
    const observer = new MutationObserver(function() {
        initializeCascadingDropdown();
    });

    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
})();
