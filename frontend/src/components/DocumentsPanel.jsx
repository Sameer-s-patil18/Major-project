import { FileText, Shield, CheckCircle, Download, Eye } from "lucide-react";

export default function DocumentsPanel() {
  return (
    <div className="min-h-screen flex items-center justify-center p-6 bg-gray-50">
      <div className="max-w-4xl w-full">
        <div className="text-center mb-12">
          <div className="bg-green-100 w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-6">
            <CheckCircle className="w-10 h-10 text-green-600" />
          </div>
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Authentication Successful!
          </h1>
          <p className="text-xl text-gray-600 mb-2">
            Welcome back! You have been successfully authenticated.
          </p>
          <div className="bg-blue-50 text-blue-800 px-4 py-2 rounded-full inline-block text-sm font-medium">
            <Shield className="w-4 h-4 inline mr-2" />
            Secure Access Granted
          </div>
        </div>

        <div className="bg-white rounded-2xl shadow-xl p-8 mb-8">
          <div className="flex items-center space-x-3 mb-6">
            <FileText className="w-8 h-8 text-blue-600" />
            <h2 className="text-2xl font-bold text-gray-900">Your Documents</h2>
          </div>
          
          <div className="text-center py-12">
            <FileText className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-700 mb-2">
              Document Access Available
            </h3>
            <p className="text-gray-500 mb-6 max-w-md mx-auto">
              Your authenticated access allows you to view, upload, and manage your secure documents.
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-xl font-medium transition-all duration-200 flex items-center justify-center space-x-2">
                <Eye className="w-5 h-5" />
                <span>View Documents</span>
              </button>
              <button className="bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-xl font-medium transition-all duration-200 flex items-center justify-center space-x-2">
                <Download className="w-5 h-5" />
                <span>Upload New</span>
              </button>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white p-6 rounded-xl shadow-lg text-center">
            <div className="bg-blue-100 w-12 h-12 rounded-lg flex items-center justify-center mx-auto mb-4">
              <Shield className="w-6 h-6 text-blue-600" />
            </div>
            <h3 className="font-semibold text-gray-900 mb-2">Secure Storage</h3>
            <p className="text-gray-600 text-sm">Your documents are encrypted and stored securely</p>
          </div>
          
          <div className="bg-white p-6 rounded-xl shadow-lg text-center">
            <div className="bg-green-100 w-12 h-12 rounded-lg flex items-center justify-center mx-auto mb-4">
              <FileText className="w-6 h-6 text-green-600" />
            </div>
            <h3 className="font-semibold text-gray-900 mb-2">Easy Access</h3>
            <p className="text-gray-600 text-sm">Access your documents anytime with face authentication</p>
          </div>
          
          <div className="bg-white p-6 rounded-xl shadow-lg text-center">
            <div className="bg-purple-100 w-12 h-12 rounded-lg flex items-center justify-center mx-auto mb-4">
              <CheckCircle className="w-6 h-6 text-purple-600" />
            </div>
            <h3 className="font-semibold text-gray-900 mb-2">Verified Identity</h3>
            <p className="text-gray-600 text-sm">Blockchain-verified authentication ensures security</p>
          </div>
        </div>

        <div className="text-center mt-12">
          <button className="text-gray-500 hover:text-gray-700 font-medium transition-colors duration-200">
            Re-authenticate →
          </button>
        </div>
      </div>
    </div>
  );
}
