import type { GlobalThemeOverrides } from 'naive-ui'

/** Friendly minimal theme: warm neutrals + teal accent (not purple). */
export const themeOverrides: GlobalThemeOverrides = {
  common: {
    fontFamily: '"Outfit", "Segoe UI", sans-serif',
    fontFamilyMono: '"IBM Plex Mono", ui-monospace, monospace',
    primaryColor: '#0F766E',
    primaryColorHover: '#0D9488',
    primaryColorPressed: '#115E59',
    primaryColorSuppl: '#14B8A6',
    successColor: '#15803D',
    warningColor: '#C2410C',
    errorColor: '#B91C1C',
    textColorBase: '#1C1917',
    textColor1: '#1C1917',
    textColor2: '#44403C',
    textColor3: '#78716C',
    borderRadius: '10px',
    borderColor: '#E7E5E4',
  },
  Button: {
    fontWeight: '600',
  },
  Card: {
    borderRadius: '16px',
  },
  Input: {
    borderRadius: '10px',
  },
  DataTable: {
    borderRadius: '12px',
  },
}
