import NavigationBar from '../navigation/NavigationBar'

export function Layout({ children }) {
  return (
    <div className="min-h-screen bg-background font-sans antialiased">
      <NavigationBar />
      <main className="container max-w-screen-2xl mx-auto py-6 px-4 md:px-6 lg:px-8">
        {children}
      </main>
      <footer className="border-t border-border/40 py-6 px-4 md:px-6 lg:px-8">
        <div className="container max-w-screen-2xl mx-auto text-sm text-muted-foreground">
          <p>© 2025 NBA Stats. All rights reserved.</p>
        </div>
      </footer>
    </div>
  )
}