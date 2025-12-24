import { motion, useInView } from 'framer-motion';
import { useRef, useState } from 'react';
import './Home.css';

function Home() {
  const [openFaq, setOpenFaq] = useState(null);
  const servicesRef = useRef(null);
  const servicesInView = useInView(servicesRef, { once: true, amount: 0.3 });

  const services = [
    {
      number: '001',
      title: 'Multimodal Ingestion',
      description: 'Upload PDFs, text, and images. Our AI structures content automatically for optimal learning.',
      categories: ['PDF Processing', 'Text Analysis', 'Image Recognition', 'Content Structuring']
    },
    {
      number: '002',
      title: 'Adaptive Tutoring',
      description: 'Intelligent explanations that adapt to your understanding level and confusion points in real-time.',
      categories: ['Personalized Learning', 'Real-time Adaptation', 'Confusion Detection', 'Interactive Explanations']
    },
    {
      number: '003',
      title: 'Practice Games',
      description: 'Engaging learning games designed for active recall and mastery of concepts through interactive practice.',
      categories: ['Active Recall', 'Game-based Learning', 'Progress Tracking', 'Mastery Assessment']
    },
    {
      number: '004',
      title: 'AI-Powered Insights',
      description: 'Get detailed insights into your learning patterns, strengths, and areas for improvement.',
      categories: ['Learning Analytics', 'Performance Metrics', 'Progress Reports', 'Personalized Recommendations']
    }
  ];

  const faqs = [
    {
      question: 'How does the adaptive tutoring work?',
      answer: 'Our AI analyzes your responses and adapts explanations in real-time based on your understanding level and confusion points.'
    },
    {
      question: 'What file types can I upload?',
      answer: 'You can upload PDFs, text documents, and images. Our AI will automatically structure the content for optimal learning.'
    },
    {
      question: 'Are the practice games personalized?',
      answer: 'Yes! Games adapt to your learning pace and focus on areas where you need the most practice.'
    },
    {
      question: 'How is my progress tracked?',
      answer: 'We provide detailed analytics showing your learning patterns, strengths, and areas for improvement with personalized recommendations.'
    }
  ];

  return (
    <div className="home">
      {/* Hero Section */}
      <section className="hero">
        <div className="hero-background">
          <img src="/image1.png" alt="E-Learning" />
        </div>
        <motion.div 
          className="hero-content"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
        >
          <motion.h1 
            className="hero-title"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
          >
            We create digital learning experiences that stand out and scale up.
          </motion.h1>
          <motion.p 
            className="hero-subtitle"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.4 }}
          >
            Through AI-powered adaptive tutoring, multimodal ingestion, and interactive practice games that turn learners into experts.
          </motion.p>
        </motion.div>

        <div className="wave-divider">
          <svg viewBox="0 0 1200 120" preserveAspectRatio="none">
            <path d="M321.39,56.44c58-10.79,114.16-30.13,172-41.86,82.39-16.72,168.19-17.73,250.45-.39C823.78,31,906.67,72,985.66,92.83c70.05,18.48,146.53,26.09,214.34,3V0H0V27.35A600.21,600.21,0,0,0,321.39,56.44Z"></path>
          </svg>
        </div>
      </section>

      {/* Services Section */}
      <section className="services-section" ref={servicesRef}>
        <div className="wave-divider-top">
          <svg viewBox="0 0 1200 120" preserveAspectRatio="none">
            <path d="M321.39,56.44c58-10.79,114.16-30.13,172-41.86,82.39-16.72,168.19-17.73,250.45-.39C823.78,31,906.67,72,985.66,92.83c70.05,18.48,146.53,26.09,214.34,3V0H0V27.35A600.21,600.21,0,0,0,321.39,56.44Z"></path>
          </svg>
        </div>

        <div className="section-card">
          <motion.h2 
          className="section-title"
          initial={{ opacity: 0, y: 20 }}
          animate={servicesInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6 }}
        >
          Services
        </motion.h2>
        <div className="services-grid">
          {services.map((service, index) => (
            <motion.div 
              key={index}
              className="service-card"
              initial={{ opacity: 0, y: 30 }}
              animate={servicesInView ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.6, delay: index * 0.15 }}
              whileHover={{ y: -5 }}
            >
              <div className="service-number">{service.number}</div>
              <h3 className="service-title">{service.title}</h3>
              <p className="service-description">{service.description}</p>
              <div className="service-categories">
                <div className="categories-label">Categories</div>
                {service.categories.map((category, catIndex) => (
                  <div key={catIndex} className="category-item">{category}</div>
                ))}
              </div>
            </motion.div>
          ))}
        </div>
        </div>

        <div className="wave-divider">
          <svg viewBox="0 0 1200 120" preserveAspectRatio="none">
            <path d="M321.39,56.44c58-10.79,114.16-30.13,172-41.86,82.39-16.72,168.19-17.73,250.45-.39C823.78,31,906.67,72,985.66,92.83c70.05,18.48,146.53,26.09,214.34,3V0H0V27.35A600.21,600.21,0,0,0,321.39,56.44Z"></path>
          </svg>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="faq-section">
        <div className="wave-divider-top">
          <svg viewBox="0 0 1200 120" preserveAspectRatio="none">
            <path d="M321.39,56.44c58-10.79,114.16-30.13,172-41.86,82.39-16.72,168.19-17.73,250.45-.39C823.78,31,906.67,72,985.66,92.83c70.05,18.48,146.53,26.09,214.34,3V0H0V27.35A600.21,600.21,0,0,0,321.39,56.44Z"></path>
          </svg>
        </div>

        <motion.h2 
          className="section-title"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
        >
          FAQ
        </motion.h2>
        <motion.p 
          className="faq-subtitle"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.2 }}
        >
          Got questions? We've got answers. Here's everything you need to know.
        </motion.p>
        <div className="faq-list">
          {faqs.map((faq, index) => (
            <motion.div 
              key={index}
              className={`faq-item ${openFaq === index ? 'open' : ''}`}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: index * 0.1 }}
            >
              <button 
                className="faq-question"
                onClick={() => setOpenFaq(openFaq === index ? null : index)}
              >
                {faq.question}
                <span className="faq-icon">{openFaq === index ? '−' : '+'}</span>
              </button>
              <motion.div 
                className="faq-answer"
                initial={false}
                animate={{ height: openFaq === index ? 'auto' : 0 }}
                transition={{ duration: 0.3 }}
              >
                <div className="faq-answer-content">{faq.answer}</div>
              </motion.div>
            </motion.div>
          ))}
        </div>

        <div className="wave-divider">
          <svg viewBox="0 0 1200 120" preserveAspectRatio="none">
            <path d="M321.39,56.44c58-10.79,114.16-30.13,172-41.86,82.39-16.72,168.19-17.73,250.45-.39C823.78,31,906.67,72,985.66,92.83c70.05,18.48,146.53,26.09,214.34,3V0H0V27.35A600.21,600.21,0,0,0,321.39,56.44Z"></path>
          </svg>
        </div>
      </section>

      {/* CTA Section */}
      <section className="cta-section">
        <div className="section-card">
          <motion.div 
            className="cta-content"
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
          >
            <h2 className="cta-title">Let's start learning</h2>
            <p className="cta-description">
              Have a topic in mind — subject, skill, or concept? Let's make learning it a reality.
            </p>
            <motion.button 
              className="cta-button"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              Get Started
            </motion.button>
          </motion.div>
        </div>
      </section>
    </div>
  );
}

export default Home;

