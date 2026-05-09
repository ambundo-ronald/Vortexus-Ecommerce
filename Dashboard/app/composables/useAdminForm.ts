interface RequiredFieldRule {
  label: string
  value: unknown
}

function isEmptyValue(value: unknown) {
  if (value === null || value === undefined)
    return true

  if (typeof value === 'string')
    return value.trim() === ''

  return false
}

export function useAdminForm() {
  function firstRequiredError(rules: RequiredFieldRule[]) {
    const missing = rules.find(rule => isEmptyValue(rule.value))
    return missing ? `${missing.label} is required.` : ''
  }

  return {
    firstRequiredError,
  }
}
