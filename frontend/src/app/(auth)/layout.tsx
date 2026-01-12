export default function AuthLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="min-h-screen flex">
      {/* Left side — form content */}
      <div className="flex flex-col justify-center w-full md:w-1/2 px-8 py-12 bg-ibook-cream">
        <div className="mx-auto w-full max-w-md">{children}</div>
      </div>

      {/* Right side — barbershop hero (hidden on mobile) */}
      <div className="hidden md:flex md:w-1/2 bg-ibook-brown-700 flex-col items-center justify-center text-white p-12">
        <div className="text-center space-y-6">
          {/* Barbershop pole illustration — CSS only */}
          <div className="flex items-center justify-center mb-8">
            <div
              className="w-10 h-40 rounded-full overflow-hidden border-4 border-white/30"
              style={{
                background:
                  'repeating-linear-gradient(180deg, #ffffff 0px, #ffffff 14px, #c0392b 14px, #c0392b 28px, #1a3a6e 28px, #1a3a6e 42px)',
              }}
            />
          </div>
          <h1 className="text-5xl font-bold text-ibook-gold-300 mb-4">IBook</h1>
          <p className="text-xl text-ibook-brown-100 text-center leading-relaxed max-w-xs">
            Your barbershop, always a tap away.
          </p>
          <div className="mt-8 text-ibook-brown-100/70 text-sm">
            Trusted by barbershops and customers everywhere
          </div>
        </div>
      </div>
    </div>
  )
}
