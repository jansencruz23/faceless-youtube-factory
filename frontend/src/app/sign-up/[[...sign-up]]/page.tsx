import { SignUp } from "@clerk/nextjs";

export default function SignUpPage() {
    return (
        <div className="flex items-center justify-center min-h-[80vh] relative">
            {/* Background gradient effects */}
            <div className="absolute inset-0 overflow-hidden pointer-events-none">
                <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/20 rounded-full blur-3xl" />
                <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl" />
            </div>

            <SignUp
                appearance={{
                    variables: {
                        colorPrimary: "#8b5cf6",
                        colorBackground: "#0a0a0a",
                        colorInputBackground: "#1a1a1a",
                        colorText: "#ffffff",
                        colorTextSecondary: "#a1a1aa",
                        colorInputText: "#ffffff",
                        borderRadius: "0.75rem",
                    },
                    elements: {
                        rootBox: "mx-auto",
                        card: "bg-black/40 backdrop-blur-xl border border-white/10 shadow-2xl shadow-primary/10",
                        headerTitle: "text-white font-bold",
                        headerSubtitle: "text-zinc-400",
                        socialButtonsBlockButton: "bg-white/5 border-white/10 hover:bg-white/10 text-white",
                        socialButtonsBlockButtonText: "text-white font-medium",
                        dividerLine: "bg-white/10",
                        dividerText: "text-zinc-500",
                        formFieldLabel: "text-zinc-300",
                        formFieldInput: "bg-white/5 border-white/10 text-white placeholder:text-zinc-500 focus:border-primary focus:ring-primary",
                        formButtonPrimary: "bg-gradient-to-r from-primary to-purple-600 hover:from-primary/90 hover:to-purple-600/90 text-white font-semibold shadow-lg shadow-primary/25",
                        footerActionLink: "text-primary hover:text-primary/80",
                        footerActionText: "text-zinc-400",
                        identityPreviewText: "text-white",
                        identityPreviewEditButton: "text-primary hover:text-primary/80",
                        formFieldAction: "text-primary hover:text-primary/80",
                        formFieldInputShowPasswordButton: "text-zinc-400 hover:text-white",
                        otpCodeFieldInput: "bg-white/5 border-white/10 text-white",
                        alert: "bg-red-500/10 border-red-500/20 text-red-400",
                        alertText: "text-red-400",
                    },
                }}
            />
        </div>
    );
}

