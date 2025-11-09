import { createContext, useContext, useState } from 'react'
import { getCookie, setCookie } from '@/lib/cookies'

// Cookie constants
const LAYOUT_COLLAPSIBLE_COOKIE_NAME = 'layout_collapsible'
const LAYOUT_VARIANT_COOKIE_NAME = 'layout_variant'
const LAYOUT_COOKIE_MAX_AGE = 60 * 60 * 24 * 7 // 7 days

// Default values
const DEFAULT_VARIANT = 'inset'
const DEFAULT_COLLAPSIBLE = 'icon'

const LayoutContext = createContext(null)

export function LayoutProvider({ children }) {
  const [collapsible, _setCollapsible] = useState(() => {
    const saved = getCookie(LAYOUT_COLLAPSIBLE_COOKIE_NAME)
    return saved || DEFAULT_COLLAPSIBLE
  })

  const [variant, _setVariant] = useState(() => {
    const saved = getCookie(LAYOUT_VARIANT_COOKIE_NAME)
    return saved || DEFAULT_VARIANT
  })

  const setCollapsible = (newCollapsible) => {
    _setCollapsible(newCollapsible)
    setCookie(LAYOUT_COLLAPSIBLE_COOKIE_NAME, newCollapsible, LAYOUT_COOKIE_MAX_AGE)
  }

  const setVariant = (newVariant) => {
    _setVariant(newVariant)
    setCookie(LAYOUT_VARIANT_COOKIE_NAME, newVariant, LAYOUT_COOKIE_MAX_AGE)
  }

  const resetLayout = () => {
    setCollapsible(DEFAULT_COLLAPSIBLE)
    setVariant(DEFAULT_VARIANT)
  }

  const contextValue = {
    resetLayout,
    defaultCollapsible: DEFAULT_COLLAPSIBLE,
    collapsible,
    setCollapsible,
    defaultVariant: DEFAULT_VARIANT,
    variant,
    setVariant,
  }

  // ✅ Use .Provider here
  return <LayoutContext.Provider value={contextValue}>{children}</LayoutContext.Provider>
}

// Hook to use the layout context
export function useLayout() {
  const context = useContext(LayoutContext)
  if (!context) {
    throw new Error('useLayout must be used within a LayoutProvider')
  }
  return context
}
