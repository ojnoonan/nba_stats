import React from 'react'

const Card = React.forwardRef(({ className, children, ...props }, ref) => {
  return (
    <div
      ref={ref}
      className={`rounded-lg border bg-card shadow-sm ${className || ''}`}
      {...props}
    >
      {children}
    </div>
  )
})

Card.displayName = "Card"

export { Card }