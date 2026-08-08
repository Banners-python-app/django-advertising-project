document.addEventListener('DOMContentLoaded', function() {
    console.log("🟢 Auto-Price & Calculator v7 (Indestructible Edition) Loaded!");

    // ==========================================
    // 1. BULLETPROOF NUMBER PARSER
    // ==========================================
    // This guarantees we never try to do math on empty text, letters, or undefined boxes
    function safeParseNum(element) {
        if (!element || element.value === undefined || element.value === '') return 0;
        const cleanString = String(element.value).replace(/,/g, '').replace(/[^\d.-]/g, '');
        const num = parseFloat(cleanString);
        return isNaN(num) ? 0 : num;
    }

    // ==========================================
    // 2. BULLETPROOF UI UPDATER
    // ==========================================
    function updateUIField(fieldName, value, labelText) {
        // Ultimate safety net: If math somehow fails, default to 0 instead of NaN
        if (isNaN(value)) value = 0; 
        
        const formattedValue = value.toFixed(2);
        const styledHtml = `<span style="color:#059669; font-weight:bold;">₹ ${formattedValue}</span>`;

        const input = document.querySelector(`input[name="${fieldName}"]`);
        if (input) { input.value = formattedValue; return; }

        const fieldRow = document.querySelector(`.field-${fieldName}`);
        if (fieldRow) {
            const divs = fieldRow.querySelectorAll('div');
            if (divs.length > 0) {
                const targetDiv = divs[divs.length - 1];
                targetDiv.innerHTML = styledHtml;
                return;
            }
        }

        const allLabels = document.querySelectorAll('label');
        for (let label of allLabels) {
            if (label.textContent.toLowerCase().includes(labelText.toLowerCase())) {
                const parent = label.parentElement.parentElement; 
                if(parent) {
                    const readonlyDiv = parent.querySelector('.readonly') || parent.querySelector('div > div:last-child');
                    if (readonlyDiv) {
                        readonlyDiv.innerHTML = styledHtml;
                        return;
                    }
                }
            }
        }
    }

    // ==========================================
    // 3. THE CALCULATOR ENGINE
    // ==========================================
    function calculateTotals() {
        let subtotal = 0;
        
        // Grab all amount inputs, but STRICTLY EXCLUDE the "gst_amount" box!
        const allAmountInputs = document.querySelectorAll('input[name$="-amount"]:not([name*="__prefix__"])');
        
        allAmountInputs.forEach(input => {
            // Skip the gst_amount box so it doesn't poison our math
            if (input.name === 'gst_amount') return; 

            // Get the row prefix (e.g., "items-0") so we can find the matching print/mount boxes
            const rowPrefix = input.name.replace('-amount', '');
            
            // Find the manual inputs on the exact same row
            const printInput = document.querySelector(`input[name="${rowPrefix}-printing_price"]`);
            const mountInput = document.querySelector(`input[name="${rowPrefix}-mounting_price"]`);

            // Safely parse the numbers
            let rent = safeParseNum(input);
            let print = safeParseNum(printInput);
            let mount = safeParseNum(mountInput);
            
            // Add them to the running total
            subtotal += (rent + print + mount);
        });

        const gst = subtotal * 0.18;
        const grandTotal = subtotal + gst;

        updateUIField('subtotal', subtotal, 'Subtotal');
        updateUIField('gst_amount', gst, 'Gst amount');
        updateUIField('grand_total', grandTotal, 'Grand total');
    }

    // ==========================================
    // 4. API FETCHER & LISTENERS
    // ==========================================
    function processDropdownChange(element) {
        const variantId = element.value;
        if (!variantId) { calculateTotals(); return; }

        const match = element.name.match(/(.+)-(\d+)-product_variant/);
        if (match) {
            const prefix = match[1];
            const rowIndex = match[2];
            const amountInput = document.querySelector(`input[name="${prefix}-${rowIndex}-amount"]`);
            
            if (!amountInput) return;

            fetch(`/orders/api/get-price/${variantId}/`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        amountInput.value = data.price;
                        amountInput.style.backgroundColor = '#d1fae5'; 
                        setTimeout(() => { amountInput.style.backgroundColor = ''; }, 600);
                        setTimeout(calculateTotals, 100);
                    }
                })
                .catch(error => console.error('🔴 API Error:', error));
        }
    }

    // Run on load
    setTimeout(calculateTotals, 600);

    // Listen for typing events
    document.addEventListener('keyup', function(e) {
        if (e.target && (
            e.target.name.endsWith('-amount') || 
            e.target.name.endsWith('-printing_price') || 
            e.target.name.endsWith('-mounting_price')
        )) {
            calculateTotals();
        }
    });
    
    // Listen for changes/clicks
    document.addEventListener('change', function(e) {
        if (e.target && (
            e.target.name.endsWith('-amount') || 
            e.target.name.endsWith('-printing_price') || 
            e.target.name.endsWith('-mounting_price')
        )) {
            calculateTotals();
        }
        if (e.target && e.target.name && e.target.name.includes('product_variant')) {
            processDropdownChange(e.target);
        }
    });

    // Unfold / Select2 jQuery hooks
    if (typeof django !== 'undefined' && django.jQuery) {
        django.jQuery(document).on('change', 'select[name*="product_variant"]', function() {
            processDropdownChange(this);
        });
    } else if (typeof window.jQuery !== 'undefined') {
        window.jQuery(document).on('change', 'select[name*="product_variant"]', function() {
            processDropdownChange(this);
        });
    }
});