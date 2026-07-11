import Image from "next/image";
import LoginForm from "@/components/auth/login-form";

export default function LoginPage() {
  return (
    <main className="login-page">
      <section className="login-brand" aria-labelledby="login-title">
        <div className="login-logo-wrap">
          <Image
            className="login-logo"
            src="/qinetra-logo.jpg"
            alt="Qinetra Laundry"
            width={1600}
            height={942}
            priority
          />
        </div>
        <p className="eyebrow">Laundry Management System</p>
        <h1 id="login-title">Keep every order on track.</h1>
        <p className="login-brand-copy">
          QLMS gives the Qinetra team one clear place to register customers,
          follow laundry orders, and prepare collections.
        </p>
      </section>

      <section className="login-form-side" aria-label="Staff login">
        <div className="login-card">
          <h2>Staff sign in</h2>
          <p className="form-intro">
            Use the username and password provided by the owner.
          </p>
          <LoginForm />
        </div>
      </section>
    </main>
  );
}
