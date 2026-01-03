import { SignUp } from "@clerk/nextjs";

export default function SignUpPage() {
    return (
        <div className="flex items-center justify-center min-h-[80vh] relative">
            {/* Background gradient effects */}
            <div className="absolute inset-0 overflow-hidden pointer-events-none">
                <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-violet-500/20 rounded-full blur-3xl" />
                <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl" />
            </div>

            <SignUp
                appearance={{
                    variables: {
                        colorPrimary: "#8b5cf6",
                        colorBackground: "#0c0a09",
                        colorInputBackground: "#1c1917",
                        colorText: "#fafaf9",
                        colorTextSecondary: "#a8a29e",
                        borderRadius: "0.75rem",
                    },
                    elements: {
                        card: "shadow-2xl shadow-violet-500/10 border border-white/10 bg-zinc-900",
                        socialButtonsBlockButton: "bg-white text-gray-900 hover:bg-gray-100 border-gray-200",
                        socialButtonsBlockButtonText: "text-gray-900 font-medium",
                        formButtonPrimary: "bg-violet-600 hover:bg-violet-500 text-white",
                        formFieldInput: "bg-zinc-800 border-zinc-700 text-white",
                        formFieldLabel: "text-zinc-300",
                        headerTitle: "text-white",
                        headerSubtitle: "text-zinc-400",
                        dividerLine: "bg-zinc-700",
                        dividerText: "text-zinc-500",
                        footerActionLink: "text-violet-400 hover:text-violet-300",
                    },
                }}
            />
        </div>
    );
}
