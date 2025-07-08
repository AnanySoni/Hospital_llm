import React from 'react';
import { Doctor } from '../types';

interface DoctorCardProps {
  doctor: Doctor;
  onSelect: (doctor: Doctor) => void;
}

const DoctorCard: React.FC<DoctorCardProps> = ({ doctor, onSelect }) => {
  // Clean up doctor name to remove duplicate "Dr." prefixes
  const cleanDoctorName = doctor.name.replace(/^Dr\.\s+Dr\.\s+/, 'Dr. ');
  const displayName = cleanDoctorName.startsWith('Dr.') ? cleanDoctorName : `Dr. ${cleanDoctorName}`;

  return (
    <div className="bg-chat-assistant border border-chat-border rounded-lg p-2 hover:bg-gray-700 transition-all duration-200 h-full">
      <div className="flex flex-col h-full">
        {/* Header with Avatar and Basic Info */}
        <div className="flex items-center space-x-2 mb-1.5">
          <div className="flex-shrink-0 w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
            <i className="fas fa-user-md text-white text-xs"></i>
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="text-xs font-semibold text-white truncate">{displayName}</h3>
            <p className="text-blue-400 text-xs font-medium truncate">{doctor.specialization}</p>
          </div>
          <div className="flex items-center space-x-1">
            {doctor.rating && (
              <div className="flex items-center space-x-1 text-yellow-400">
                <i className="fas fa-star text-xs"></i>
                <span className="text-xs font-medium">{doctor.rating}</span>
              </div>
            )}
            {/* Calendar sync indicator - assuming this info comes from backend */}
            <div className="flex items-center">
              <i className="fas fa-calendar text-green-500 text-xs" title="Calendar sync enabled"></i>
            </div>
          </div>
        </div>

        {/* Reason for recommendation */}
        <p className="text-gray-300 text-xs mb-1.5 leading-relaxed line-clamp-2">
          {doctor.reason}
        </p>

        {/* Experience and Details */}
        <div className="space-y-0.5 mb-1.5 flex-1">
          <div className="flex items-center space-x-1.5 text-gray-400 text-xs">
            <i className="fas fa-briefcase w-3"></i>
            <span className="truncate">{doctor.experience}</span>
          </div>
          {doctor.location && (
            <div className="flex items-center space-x-1.5 text-gray-400 text-xs">
              <i className="fas fa-map-marker-alt w-3"></i>
              <span className="truncate">{doctor.location}</span>
            </div>
          )}
          {doctor.availability && (
            <div className="flex items-center space-x-1.5 text-green-400 text-xs">
              <i className="fas fa-clock w-3"></i>
              <span className="truncate">{doctor.availability}</span>
            </div>
          )}
        </div>

        {/* Expertise Tags - Limited to 2 */}
        {doctor.expertise && doctor.expertise.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-2">
            {doctor.expertise.slice(0, 2).map((tag, index) => (
              <span
                key={index}
                className="bg-blue-900 text-blue-300 text-xs px-1.5 py-0.5 rounded-full truncate"
              >
                {tag}
              </span>
            ))}
            {doctor.expertise.length > 2 && (
              <span className="text-gray-400 text-xs px-1">
                +{doctor.expertise.length - 2}
              </span>
            )}
          </div>
        )}

        {/* Select Button */}
        <button
          onClick={() => onSelect(doctor)}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-1.5 px-2 rounded-md transition-colors duration-200 flex items-center justify-center space-x-1.5 text-xs"
        >
          <i className="fas fa-calendar-check text-xs"></i>
          <span>Book Appointment</span>
        </button>
      </div>
    </div>
  );
};

export default DoctorCard; 