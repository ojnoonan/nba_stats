import { Fragment } from 'react'
import { Dialog as HeadlessDialog, Transition } from '@headlessui/react'

export function Dialog({ isOpen, onClose, children }) {
  return (
    <Transition appear show={isOpen} as={Fragment}>
      <HeadlessDialog as="div" className="relative z-50" onClose={onClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-background/80 backdrop-blur-sm" />
        </Transition.Child>

        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4 text-center">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <HeadlessDialog.Panel 
                className="w-full max-w-md transform overflow-hidden rounded-lg bg-card text-card-foreground p-6 shadow-xl transition-all 
                animate-fade-in animate-slide-up"
              >
                {children}
              </HeadlessDialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </HeadlessDialog>
    </Transition>
  )
}

Dialog.Title = function DialogTitle({ children, className = '' }) {
  return (
    <HeadlessDialog.Title
      className={`text-lg font-medium leading-6 text-primary mb-4 ${className}`}
    >
      {children}
    </HeadlessDialog.Title>
  )
}

Dialog.Description = function DialogDescription({ children, className = '' }) {
  return (
    <HeadlessDialog.Description
      className={`text-sm text-muted-foreground mb-4 ${className}`}
    >
      {children}
    </HeadlessDialog.Description>
  )
}