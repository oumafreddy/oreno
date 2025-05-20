/**
 * Oreno GRC Modal Context Handler
 * Enhances dropdown filtering based on URL context
 * Works with modal-handler.js to provide contextual filtering
 */

document.addEventListener('DOMContentLoaded', function() {
    // Listen for modal content loading
    document.body.addEventListener('htmx:afterSwap', function(event) {
        if (event.detail.target && event.detail.target.id === 'modal-body') {
            enhanceContextualFiltering(event.detail.target);
        }
    });
    
    // Also enhance any forms that exist on page load
    document.querySelectorAll('form').forEach(function(form) {
        enhanceContextualFiltering(form);
    });
});

/**
 * Extract context parameters from URL and current page
 */
function getContextParameters() {
    const url = window.location.href;
    const context = {};
    
    // Extract engagement_pk
    const engagementMatch = url.match(/engagements\/(\d+)/);
    if (engagementMatch) {
        context.engagement_pk = engagementMatch[1];
    }
    
    // Extract objective_pk
    const objectiveMatch = url.match(/objectives\/(\d+)/);
    if (objectiveMatch) {
        context.objective_pk = objectiveMatch[1];
    }
    
    // Extract procedure_pk
    const procedureMatch = url.match(/procedures\/(\d+)/);
    if (procedureMatch) {
        context.procedure_pk = procedureMatch[1];
    }
    
    // Extract issue_pk
    const issueMatch = url.match(/issues\/(\d+)/);
    if (issueMatch) {
        context.issue_pk = issueMatch[1];
    }
    
    // Look for hidden context fields that might be present in the page
    const contextInputs = document.querySelectorAll('[data-context-type]');
    contextInputs.forEach(function(input) {
        const type = input.getAttribute('data-context-type');
        const value = input.value;
        if (type && value) {
            context[type] = value;
        }
    });
    
    return context;
}

/**
 * Enhance form dropdown filtering based on context
 */
function enhanceContextualFiltering(container) {
    const context = getContextParameters();
    if (Object.keys(context).length === 0) return; // No context to apply
    
    const form = container.querySelector('form') || container;
    if (!form) return;
    
    // Process select elements that could benefit from contextual filtering
    const selects = form.querySelectorAll('select');
    selects.forEach(function(select) {
        const name = select.name.toLowerCase();
        
        // Apply contextual filtering based on field name and available context
        if (name.includes('objective') && context.engagement_pk) {
            filterSelectByContext(select, 'data-engagement', context.engagement_pk);
        }
        else if (name.includes('procedure') && (context.objective_pk || context.engagement_pk)) {
            if (context.objective_pk) {
                filterSelectByContext(select, 'data-objective', context.objective_pk);
            } else {
                filterSelectByContext(select, 'data-engagement', context.engagement_pk);
            }
        }
        else if (name.includes('result') && (context.procedure_pk || context.objective_pk)) {
            if (context.procedure_pk) {
                filterSelectByContext(select, 'data-procedure', context.procedure_pk);
            } else {
                filterSelectByContext(select, 'data-objective', context.objective_pk);
            }
        }
        else if (name.includes('issue') && (context.procedure_pk || context.objective_pk || context.engagement_pk)) {
            if (context.procedure_pk) {
                filterSelectByContext(select, 'data-procedure', context.procedure_pk);
            } else if (context.objective_pk) {
                filterSelectByContext(select, 'data-objective', context.objective_pk);
            } else {
                filterSelectByContext(select, 'data-engagement', context.engagement_pk);
            }
        }
    });
    
    // If we have context for the parent object in a hierarchical relationship,
    // try to auto-select it and possibly hide it
    tryAutoSelectParentField(form, context);
}

/**
 * Filter select options based on a data attribute context
 */
function filterSelectByContext(select, dataAttr, value) {
    let hasVisibleOptions = false;
    
    // Count visible options before filtering
    const options = select.querySelectorAll('option');
    let initialVisible = 0;
    options.forEach(function(option) {
        if (option.value && !option.disabled) initialVisible++;
    });
    
    // Only apply filtering if we have multiple options
    if (initialVisible <= 1) return;
    
    options.forEach(function(option) {
        if (!option.value) return; // Skip empty options like "-----"
        
        const attrValue = option.getAttribute(dataAttr);
        if (attrValue && attrValue !== value) {
            option.style.display = 'none';
            option.disabled = true;
        } else {
            option.style.display = '';
            option.disabled = false;
            hasVisibleOptions = true;
        }
    });
    
    // If we filtered out all options, restore them to avoid empty dropdowns
    if (!hasVisibleOptions) {
        options.forEach(function(option) {
            option.style.display = '';
            option.disabled = false;
        });
    }
}

/**
 * Try to auto-select parent field based on context
 */
function tryAutoSelectParentField(form, context) {
    // Map context keys to form field names
    const fieldMapping = {
        'engagement_pk': ['engagement', 'engagement_id'],
        'objective_pk': ['objective', 'objective_id'],
        'procedure_pk': ['procedure', 'procedure_id'],
        'issue_pk': ['issue', 'issue_id']
    };
    
    // For each context parameter we have
    Object.keys(context).forEach(function(contextKey) {
        const value = context[contextKey];
        const possibleFields = fieldMapping[contextKey] || [];
        
        // Check if any of the possible fields exist in the form
        possibleFields.forEach(function(fieldName) {
            const field = form.querySelector(`[name="${fieldName}"]`);
            if (field) {
                // Set the value and make it read-only if it's the only option
                field.value = value;
                
                // If it's a select with only this option or empty option
                if (field.tagName === 'SELECT') {
                    const options = field.querySelectorAll('option[value]');
                    if (options.length === 1 || 
                        (options.length === 2 && options[0].value === '')) {
                        field.setAttribute('readonly', 'readonly');
                        // Hide the parent div or add a disabled appearance
                        const formGroup = field.closest('.form-group') || field.closest('.mb-3');
                        if (formGroup) {
                            formGroup.classList.add('opacity-75');
                            const label = formGroup.querySelector('label');
                            if (label) {
                                label.innerHTML += ' <small class="text-muted">(Auto-selected)</small>';
                            }
                        }
                    }
                }
            }
        });
    });
}
