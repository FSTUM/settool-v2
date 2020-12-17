// eslint-disable-next-line no-unused-vars
const addLink = (parent, label, callback) => {
    const a = document.createElement('a');
    a.href = '#';
    a.text = label;
    $(a).click(callback);
    $(a).insertAfter(parent);
};

// eslint-disable-next-line no-unused-vars
const defaultCallback = (action) => {
    return () => {
        $(this).parent().find('select[multiple]').multiSelect(action);
        return false;
    };
};

// eslint-disable-next-line no-unused-vars
const valueCallback = (action, value) => {
    return () => {
        const elements = $(this)
            .parent()
            .find('select[multiple]')
            .find('option')
            .map((idx, option) => {
                if ($(option).text().toLowerCase().includes(value)) {
                    return option.value;
                }
                return null;
            });

        $(this).parent().find('select[multiple]').multiSelect(action, elements);
        return false;
    };
};
