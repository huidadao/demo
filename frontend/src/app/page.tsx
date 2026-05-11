export default function Home() {
  return (
    <main className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Welcome to the App
        </h1>
        <p className="text-gray-600 mb-8">
          Please login or register to continue
        </p>
        <div className="space-x-4">
          <a
            href="/login"
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Login
          </a>
          <a
            href="/register"
            className="px-6 py-3 bg-gray-200 text-gray-900 rounded-lg hover:bg-gray-300"
          >
            Register
          </a>
        </div>
      </div>
    </main>
  );
}