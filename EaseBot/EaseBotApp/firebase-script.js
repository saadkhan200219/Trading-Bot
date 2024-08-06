import { initializeApp } from "https://www.gstatic.com/firebasejs/9.4.0/firebase-app.js";
import { getAuth, createUserWithEmailAndPassword, signInWithEmailAndPassword, onAuthStateChanged } from "https://www.gstatic.com/firebasejs/9.4.0/firebase-auth.js";

const firebaseConfig = {
  apiKey: "AIzaSyBoLsSmfgx3co6HOCWpEMY7lfWAgX-z5Z4",
  authDomain: "talkgenius-77644.firebaseapp.com",
  projectId: "talkgenius-77644",
  storageBucket: "talkgenius-77644.appspot.com",
  messagingSenderId: "639644293009",
  appId: "1:639644293009:web:f82cf6661d2f9f552f2c30"
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

const loginForm = document.getElementById('login-form');
const signupForm = document.getElementById('signup-form');
const logoutButton = document.getElementById('logout-button');

if (signupForm) {
  signupForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const up_Email = document.querySelector(".up-email").value;
    const up_Password = document.querySelector(".up-password").value;

    createUserWithEmailAndPassword(auth, up_Email, up_Password)
      .then((userCredential) => {
        window.location.href = 'index.html';
      })
      .catch((error) => {
        console.log(error.code);
        alert(error.message);
      });
  });
}

if (loginForm) {
  loginForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const in_Email = document.querySelector(".in-email").value;
    const in_Password = document.querySelector(".in-password").value;

    signInWithEmailAndPassword(auth, in_Email, in_Password)
      .then((userCredential) => {
        window.location.href = 'home.html';
      })
      .catch((error) => {
        console.log(error.code);
        alert(error.message);
      });
  });
}


if (logoutButton) {
  logoutButton.addEventListener('click', () => {
    auth.signOut().then(() => {
      console.log('User signed out');
      window.location.href = 'index.html';
    }).catch((error) => {
      console.error('Sign out error', error);
    });
  });
}

function checkAuth() {
  console.log("Checking authentication state...");
  onAuthStateChanged(auth, (user) => {
    console.log(user);
    if (!user && window.location.pathname !== '/EaseBotApp/index.html') {
      console.log("No user is signed in. Redirecting to index.html");
      window.location.href = 'index.html';
    }
  });
}

window.onload = checkAuth;
